"""src/api/models.py

Carga los artefactos entrenados y produce el plan de distribución.

Reutiliza la maquinaria probada del repositorio (``src.modeling`` y
``fleet_loading``): canonicalización, tensores por par, ``BlockScaler``
guardado en ``pairwise_schema.json`` y el decoder con capacidad. Nada de esto se
reimplementa aquí; este módulo sólo orquesta lo existente para un único
manifiesto.

Los tres modelos servidos (XGBoost, LightGBM y attention) son *pairwise*: el
eje de camiones es dinámico, así que **no hay límite de camiones ni de
capacidad**. La única diferencia entre ellos es cómo se cargan los logits.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

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

# Política de decodificación por defecto (objetivo primario: contar vehículos).
DEFAULT_POLICY = "count"


class ModelUnavailableError(RuntimeError):
    pass


class ModelService:
    """Carga un artefacto una vez y sirve planes de distribución."""

    def __init__(self, model_name: str = "xgboost") -> None:
        self.model_name = model_name
        self.artifact_dir = ARTIFACT_ROOT / model_name
        if not self.artifact_dir.exists():
            raise ModelUnavailableError(
                f"No hay artefactos para el modelo {model_name!r} en {self.artifact_dir}"
            )

        schema = json.loads(
            (self.artifact_dir / "pairwise_schema.json").read_text(encoding="utf-8")
        )
        self.classes: list[str] = schema["classes"]
        self.scaler = BlockScaler.from_dict(schema["blocks"])
        self._policy = self._load_policy()

        if model_name == "attention":
            self._classifier = None
            self._predict_proba: Callable | None = None
        else:
            import joblib

            self._classifier = joblib.load(self.artifact_dir / "classifier.joblib")
            self._predict_proba = lambda x: np.asarray(self._classifier.predict_proba(x))

    def _load_policy(self) -> str:
        """Política registrada en los resultados medidos, si existe."""
        stem = {"xgboost": "xgb", "lightgbm": "lgb", "attention": "att"}.get(
            self.model_name, self.model_name[:3]
        )
        results = ARTIFACT_ROOT / "results" / f"{stem}_results.json"
        if not results.exists():
            return DEFAULT_POLICY
        payload = json.loads(results.read_text(encoding="utf-8"))
        return payload.get(f"{stem}_decoder_policy", DEFAULT_POLICY)

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

        episodes_tensors = [e for e in episodes]
        return stack_episode_logits(
            episodes,
            arrays,
            {i: logits_from_proba(ep, self.scaler, self._predict_proba) for i, ep in enumerate(episodes_tensors)},
        )

    def distribute(
        self,
        vehicles: list[dict],
        fleet: list[float],
    ) -> tuple[list[dict], list[int]]:
        """Asigna cada vehículo a un camión canónico (o difiere).

        Devuelve ``(plan, assignment)``:
        * ``plan`` -- lista de camiones en orden canónico con sus vehículos.
        * ``assignment`` -- índice canónico del camión por vehículo; ``-1`` =
          diferido (``DEFERRED``).

        Los vehículos se devuelven en el orden en que entraron, pero el plan
        mantiene el orden canónico de camiones (capacidad descendente).
        """
        if not vehicles:
            raise ValueError("No hay vehículos para distribuir")
        if not fleet:
            raise ValueError("La flota está vacía")

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

        sorted_vehicles = sorted(
            enumerate(vehicles), key=lambda iv: iv[1]["identificador"]
        )
        for model_pos, (orig_idx, v) in enumerate(sorted_vehicles):
            truck_idx = decoded.assignment[model_pos]
            entry = {
                "identificador": v["identificador"],
                "clase": v["clase"],
                "cu": v["cu"],
                "canton": v["canton"],
            }
            if truck_idx == DEFERRED:
                continue
            trucks[truck_idx]["vehicles"].append(entry)

        return trucks, decoded.assignment.tolist()
