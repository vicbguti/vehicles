"""src/api/models.py

Carga los artefactos entrenados y produce el plan de distribución.

Reutiliza la maquinaria probada del repositorio (``src.modeling`` y
``fleet_loading``): canonicalización, tensores por par, ``BlockScaler``
guardado en ``pairwise_schema.json`` y el decoder con capacidad. Nada de esto se
reimplementa aquí; este módulo sólo orquesta lo existente para un único
manifiesto.

Se sirven los seis modelos del repositorio. Cuatro son *pairwise* (XGBoost,
LightGBM, el transformer de atención y el MLP de Keras): su eje de camiones es
dinámico, así que **no hay límite de camiones ni de capacidad**. RF y la
regresión logística son de ancho fijo (flota rellenada a ``max_trucks``), así
que **sólo sirven flotas de hasta ese tope**; más allá, el API responde un
error claro en vez de un plan inválido.

La diferencia entre modelos está sólo en cómo se cargan los logits:

* XGBoost y LightGBM: clasificador binario por filas de opción
  (`logits_from_proba`).
* Attention: head de atención sobre `(vehículo, camión)`.
* MLP: puntúa el lote completo (`pair_features`, `defer_features`,
  `mask_bias`) y devuelve logits crudos, igual que `scripts/evaluate_mlp.py`.
  Requiere Keras (usa el backend de torch si no hay TensorFlow).
* RF y logreg: clasificador multiclase de ancho fijo (`FlatArrays` +
  `predict_proba`), igual que `scripts/train_classical.py`.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "fleet_loading" / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "fleet_loading" / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.modeling.canonicalization import canonicalize_fleet  # noqa: E402
from src.modeling.capacity_decoder import DEFERRED, decode_episode  # noqa: E402
from src.modeling.features import BlockScaler  # noqa: E402
from src.modeling.metrics import episode_logits  # noqa: E402

ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "fleet_loading"

# El MLP vive en artifacts/mlp/ con otro formato de artefacto; los clásicos
# (RF, logreg), en artifacts/<modelo>/ con feature_schema.json plano; el resto,
# en artifacts/fleet_loading/<modelo>/ con pairwise_schema.json.
ARTIFACT_DIRS = {
    "xgboost": ARTIFACT_ROOT / "xgboost",
    "lightgbm": ARTIFACT_ROOT / "lightgbm",
    "attention": ARTIFACT_ROOT / "attention",
    "mlp": REPO_ROOT / "artifacts" / "mlp",
    "rf": REPO_ROOT / "artifacts" / "rf",
    "logreg": REPO_ROOT / "artifacts" / "logreg",
}
SCHEMA_FILES = {
    "xgboost": "pairwise_schema.json",
    "lightgbm": "pairwise_schema.json",
    "attention": "pairwise_schema.json",
    "mlp": "feature_schema.json",
    "rf": "feature_schema.json",
    "logreg": "feature_schema.json",
}
# Los de ancho fijo sólo admiten flotas de hasta `max_trucks` camiones.
FLAT_MODELS = {"rf", "logreg"}

# Política de decodificación por defecto (objetivo primario: contar vehículos).
DEFAULT_POLICY = "count"

# Keras 3 sin TensorFlow usa el backend de torch (ya presente en el entorno).
os.environ.setdefault("KERAS_BACKEND", "torch")


class ModelUnavailableError(RuntimeError):
    pass


class ModelService:
    """Carga un artefacto una vez y sirve planes de distribución."""

    def __init__(self, model_name: str = "xgboost") -> None:
        self.model_name = model_name
        if model_name not in ARTIFACT_DIRS:
            raise ModelUnavailableError(
                f"Modelo desconocido: {model_name!r}. Opciones: {sorted(ARTIFACT_DIRS)}"
            )
        self.artifact_dir = ARTIFACT_DIRS[model_name]
        if not self.artifact_dir.exists():
            raise ModelUnavailableError(
                f"No hay artefactos para el modelo {model_name!r} en {self.artifact_dir}"
            )

        schema = json.loads(
            (self.artifact_dir / SCHEMA_FILES[model_name]).read_text(encoding="utf-8")
        )
        self.classes: list[str] = schema["classes"]
        self.scaler = BlockScaler.from_dict(schema["blocks"])
        # Los clásicos son de ancho fijo: su tope es parte del artefacto.
        self.max_trucks: int | None = (
            int(schema["max_trucks_padding"]) if model_name in FLAT_MODELS else None
        )
        self._policy = self._load_policy()

        if model_name == "mlp":
            import keras

            self._classifier = keras.models.load_model(self.artifact_dir / "model.keras")
            self._predict_proba: Callable | None = None
        elif model_name == "attention":
            self._classifier = None
            self._predict_proba: Callable | None = None
        elif model_name in FLAT_MODELS:
            import joblib

            self._classifier = joblib.load(self.artifact_dir / "model.joblib")
            self._predict_proba: Callable | None = None
        else:
            import joblib

            self._classifier = joblib.load(self.artifact_dir / "classifier.joblib")
            self._predict_proba = lambda x: np.asarray(self._classifier.predict_proba(x))

    def _load_policy(self) -> str:
        """Política registrada en los resultados medidos, si existe."""
        if self.model_name == "mlp":
            results = self.artifact_dir / "metrics.json"
            key = "decoder_policy_selected"
        elif self.model_name in FLAT_MODELS:
            # La política viaja dentro del propio feature_schema.json plano.
            results = self.artifact_dir / "feature_schema.json"
            key = "decoder_policy"
        else:
            stem = {"xgboost": "xgb", "lightgbm": "lgb", "attention": "att"}[self.model_name]
            results = ARTIFACT_ROOT / "results" / f"{stem}_results.json"
            key = f"{stem}_decoder_policy"
        if not results.exists():
            return DEFAULT_POLICY
        payload = json.loads(results.read_text(encoding="utf-8"))
        return payload.get(key, DEFAULT_POLICY)

    def _episode_from_manifest(
        self,
        vehicles: list[dict],
        fleet: list[float],
    ) -> tuple[list, object]:
        """Construye el DataFrame de un episodio y los tensores del modelo.

        `fleet` llega en el orden del operador; se canonicaliza por capacidad
        descendente igual que en entrenamiento.
        """
        rows = [
            {
                "episode_id": "api",
                "uid": v["identificador"],
                "clase": v["clase"],
                "cu": float(v["cu"]),
                "truck": "SIN_CAMION",
                "loaded": True,
            }
            for v in vehicles
        ]
        joined = pd.DataFrame(rows)
        joined["truck_capacities"] = [list(fleet)] * len(joined)
        joined["n_loaded"] = len(joined)
        joined["cu_utilized"] = joined["cu"].sum()
        joined["optimal"] = True

        from fleet_loading.pipelines.training.pairwise import build_tensors

        episodes, arrays, _ = build_tensors(joined, self.classes, self.scaler)
        return episodes, arrays

    def _logits(self, episodes: list, arrays: object) -> np.ndarray:
        """Logits ``(V, 1+T)`` por episodio según el tipo de modelo."""
        from fleet_loading.pipelines.training.pairwise import (
            logits_from_proba,
            stack_episode_logits,
        )

        if self.model_name in FLAT_MODELS:
            # Clasificador multiclase: X plano, una fila por vehículo, y la
            # probabilidad ya viene en el espacio canónico (0 = SIN_CAMION,
            # 1..max_trucks). Las columnas de relleno se recortan al decodificar.
            from src.modeling.flat_features import build_flat_arrays

            flat = build_flat_arrays(episodes, self.scaler, self.max_trucks)
            return np.asarray(self._classifier.predict_proba(flat.X))

        if self.model_name == "mlp":
            # El MLP puntúa el lote completo con sus tres entradas y devuelve
            # logits crudos (B, 1+T) ya en el espacio canónico. Mismo flujo que
            # scripts/evaluate_mlp.py (modo extrapolación).
            from src.modeling.features import as_model_inputs

            return np.asarray(self._classifier.predict(as_model_inputs(arrays), verbose=0))

        if self.model_name == "attention":
            import torch
            from fleet_loading.pipelines.training.attention_model import (
                PairwiseAttentionModel,
                collate_episodes,
            )

            ckpt = torch.load(
                self.artifact_dir / "model.pt",
                map_location="cpu",
                weights_only=False,
            )
            cfg = ckpt["model_config"]
            model = PairwiseAttentionModel(
                vehicle_dim=cfg["vehicle_dim"],
                truck_dim=cfg["truck_dim"],
                context_dim=cfg["context_dim"],
                d_model=cfg["d_model"],
                nhead=cfg["nhead"],
                num_layers=cfg["num_layers"],
                dropout=cfg["dropout"],
            )
            model.load_state_dict(ckpt["model_state_dict"])
            model.eval()

            logits_by_ep = {}
            with torch.no_grad():
                for i, ep in enumerate(episodes):
                    item = {
                        "vehicle": torch.from_numpy(
                            self.scaler.transform("vehicle", ep.vehicle).astype(np.float32)
                        ),
                        "truck": torch.from_numpy(
                            self.scaler.transform("truck", ep.truck).astype(np.float32)
                        ),
                        "context": torch.from_numpy(
                            self.scaler.transform("context", ep.context[None, :])[0].astype(
                                np.float32
                            )
                        ),
                        "labels": torch.from_numpy(ep.target.astype(np.int64)),
                        "cu": torch.from_numpy(ep.cu.astype(np.float32)),
                        "capacities": torch.from_numpy(ep.capacities.astype(np.float32)),
                        "episode_id": ep.episode_id,
                        "n_trucks": ep.n_trucks,
                        "teacher_n_loaded": ep.teacher_n_loaded,
                        "teacher_cu_utilized": ep.teacher_cu_utilized,
                    }
                    batch = collate_episodes([item])
                    out = model(batch)[0]
                    logits_by_ep[i] = out[: ep.n_vehicles, : ep.n_trucks + 1].numpy()
            return stack_episode_logits(
                episodes,
                arrays,
                logits_by_ep,
            )

        return stack_episode_logits(
            episodes,
            arrays,
            {
                i: logits_from_proba(ep, self.scaler, self._predict_proba)
                for i, ep in enumerate(episodes)
            },
        )

    def distribute(
        self,
        vehicles: list[dict],
        fleet: list[float],
    ) -> tuple[list[dict], list[int]]:
        """Asigna cada vehículo a un camión canónico (o difiere).

        Devuelve ``(plan, assignment)``:
        * ``plan`` -- lista de camiones en orden canónico con sus vehículos.
        * ``assignment`` -- índice canónico del camión **por vehículo en el
          orden de entrada**; ``-1`` = diferido (``DEFERRED``).

        Los vehículos se devuelven en el orden en que entraron, pero el plan
        mantiene el orden canónico de camiones (capacidad descendente).
        """
        if not vehicles:
            raise ValueError("No hay vehículos para distribuir")
        if not fleet:
            raise ValueError("La flota está vacía")

        if self.model_name in FLAT_MODELS and len(fleet) > (self.max_trucks or 0):
            raise ValueError(
                f"El modelo {self.model_name!r} es de ancho fijo: soporta hasta "
                f"{self.max_trucks} camiones y la flota tiene {len(fleet)}. Usa un "
                "modelo pairwise (xgboost, lightgbm, attention o mlp) para esta flota."
            )

        episodes, arrays = self._episode_from_manifest(vehicles, fleet)
        ep = episodes[0]
        logits = self._logits(episodes, arrays)
        rows = np.flatnonzero(arrays.episode_index == 0)
        ep_lg = episode_logits(logits, rows, ep.n_trucks)

        decoded = decode_episode(
            ep_lg,
            cu=ep.cu,
            capacities=ep.capacities,
            policy=self._policy,
        )

        fleet = canonicalize_fleet(fleet)
        trucks: list[dict] = [
            {
                "id": f"camion-{i + 1}",
                "capacity": cap,
                "vehicles": [],
            }
            for i, cap in enumerate(fleet.capacities)
        ]

        sorted_vehicles = sorted(enumerate(vehicles), key=lambda iv: iv[1]["identificador"])
        # `decode_episode` devuelve la asignación en el orden interno de filas
        # del modelo, que en ambos tipos es uid ascendente. Se reindexa al
        # orden de entrada para que el plan y el `assignment` devuelto queden
        # siempre alineados con `vehicles`.
        per_vehicle = np.empty(len(vehicles), dtype=int)
        for model_pos, (orig_idx, v) in enumerate(sorted_vehicles):
            truck_idx = decoded.assignment[model_pos]
            per_vehicle[orig_idx] = truck_idx
            if truck_idx == DEFERRED:
                continue
            trucks[truck_idx]["vehicles"].append(
                {
                    "identificador": v["identificador"],
                    "clase": v["clase"],
                    "cu": v["cu"],
                    "canton": v["canton"],
                }
            )

        return trucks, per_vehicle.tolist()
