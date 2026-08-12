#!/usr/bin/env python3
"""Evalúa los tres modelos fleet_loading (XGBoost, LightGBM, atención) sobre
conjuntos extrapolados con flotas MÁS GRANDES que las del entrenamiento.

Cada modelo es por pares: emite logits ``(V, 1 + T)`` con el eje de camiones
``None`` en la arquitectura, así que los mismos pesos atienden cualquier ``T``.
Este script mide si esa propiedad estructural se cumple de verdad: evalúa las
puntuaciones guardadas por ``_save_model_artifact`` sobre
``data/episodes/extrap_*`` y reporta las agregadas de ``src.modeling.metrics``
(modelo + greedy) más la latencia de decodificación.

Uso (desde la raíz del repositorio)::

    uv run python scripts/evaluate_fleet_loading.py --model xgb \
        --episodes-dir data/episodes/extrap_5_6_same
    uv run python scripts/evaluate_fleet_loading.py --model attention \
        --episodes-dir data/episodes/extrap_8_10_constanttotal
    uv run python scripts/evaluate_fleet_loading.py --model all \
        --episodes-dir data/episodes/extrap_5_6_same
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "fleet_loading" / "src"))

import numpy as np  # noqa: E402
from fleet_loading.pipelines.training.pairwise import (  # noqa: E402
    build_tensors,
    derive_classes,
    logits_from_proba,
    measure_latency,
    stack_episode_logits,
)

from src.modeling.dataset import load_episode_tables  # noqa: E402
from src.modeling.features import BlockScaler  # noqa: E402
from src.modeling.metrics import aggregate, evaluate_greedy, evaluate_model  # noqa: E402

ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "fleet_loading"
DEFAULT_EPISODES_DIR = REPO_ROOT / "data" / "episodes"


def load_joined(episodes_dir: Path) -> object:
    return load_episode_tables(
        episodes_dir / "episodes.parquet", episodes_dir / "episode_vehicles.parquet"
    )


def attention_logits(episodes, scaler) -> dict[str, np.ndarray]:
    """Logits ``(V, 1 + T)`` por episodio, indexados por ``episode_id``."""
    import torch
    from fleet_loading.pipelines.training.attention_model import (
        PairwiseAttentionModel,
        collate_episodes,
    )

    ckpt = torch.load(ARTIFACT_ROOT / "attention" / "model.pt", map_location="cpu")
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
        for ep in episodes:
            item = {
                "vehicle": torch.from_numpy(
                    scaler.transform("vehicle", ep.vehicle).astype(np.float32)
                ),
                "truck": torch.from_numpy(scaler.transform("truck", ep.truck).astype(np.float32)),
                "context": torch.from_numpy(
                    scaler.transform("context", ep.context[None, :])[0].astype(np.float32)
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
            logits_by_ep[ep.episode_id] = out[: ep.n_vehicles, : ep.n_trucks + 1].numpy()
    return logits_by_ep


def evaluate_model_on(
    model_name: str,
    episodes_dir: Path,
    policy: str | None,
) -> dict:
    joined = load_joined(episodes_dir)
    classes = derive_classes(joined)

    schema = json.loads(
        (ARTIFACT_ROOT / model_name / "pairwise_schema.json").read_text(encoding="utf-8")
    )
    scaler = BlockScaler.from_dict(schema["blocks"])

    episodes, arrays, _ = build_tensors(joined, classes, scaler)

    if model_name == "attention":
        logits_by_ep = attention_logits(episodes, scaler)
        logits = stack_episode_logits(
            episodes,
            arrays,
            {i: logits_by_ep[ep.episode_id] for i, ep in enumerate(episodes)},
        )
    else:
        import joblib

        classifier = joblib.load(ARTIFACT_ROOT / model_name / "classifier.joblib")

        def predict_proba(x: np.ndarray) -> np.ndarray:
            return np.asarray(classifier.predict_proba(x))

        logits = stack_episode_logits(
            episodes,
            arrays,
            {i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(episodes)},
        )

    n_classes = len(classes)
    n_labels = arrays.max_trucks + 1

    if policy is None:
        from fleet_loading.pipelines.training.pairwise import select_policy

        policy = select_policy(episodes, arrays, logits, n_classes)
    model_metrics = aggregate(evaluate_model(episodes, arrays, logits, policy, n_classes), n_labels)
    greedy_metrics = aggregate(evaluate_greedy(episodes, arrays, n_classes), n_labels)
    latency = measure_latency(episodes, arrays, logits, policy)

    payload = {
        "generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "model": model_name,
        "episodes_dir": str(episodes_dir),
        "decoder_policy": policy,
        "max_trucks_in_set": arrays.max_trucks,
        "max_trucks_seen_in_training": int(schema["max_trucks_padding"]),
        "model_metrics": model_metrics,
        "baseline_greedy": greedy_metrics,
        "inference_latency_per_manifest": latency,
    }
    out = ARTIFACT_ROOT / model_name / f"extrap_{episodes_dir.name}_metrics.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\n=== {model_name} sobre {episodes_dir.name} "
        f"({model_metrics['n_episodes']:,} episodios, {model_metrics['n_vehicle_rows']:,} filas)"
    )
    print(
        f"  Camiones en el conjunto: hasta {arrays.max_trucks} "
        f"(el entrenamiento vio hasta {schema['max_trucks_padding']})"
    )
    print(
        f"  1. Violación de capacidad   modelo {model_metrics['capacity_violation_rate']:.4f}   "
        f"greedy {greedy_metrics['capacity_violation_rate']:.4f}"
    )
    print(
        f"  2. Brecha de conteo (media) modelo {model_metrics['loaded_gap_mean']:+.4f}   "
        f"greedy {greedy_metrics['loaded_gap_mean']:+.4f}"
    )
    print(
        f"     Iguala el óptimo         modelo "
        f"{model_metrics['episodes_matching_teacher_count_pct']:.2f}%  "
        f"greedy {greedy_metrics['episodes_matching_teacher_count_pct']:.2f}%"
    )
    print(
        f"  3. Brecha de CU (media)     modelo {model_metrics['cu_gap_mean']:+.4f}   "
        f"greedy {greedy_metrics['cu_gap_mean']:+.4f}"
    )
    print(
        f"     Utilización              modelo {model_metrics['cu_utilization_model_pct']:.2f}%  "
        f"greedy {greedy_metrics['cu_utilization_model_pct']:.2f}%  "
        f"maestro {model_metrics['cu_utilization_teacher_pct']:.2f}%"
    )
    print(
        f"  5. F1 macro                 modelo {model_metrics['macro_f1']:.4f}   "
        f"greedy {greedy_metrics['macro_f1']:.4f}"
    )
    print(
        f"     Concordancia por clase   modelo "
        f"{model_metrics['class_level_agreement_mean']:.4f}   "
        f"greedy {greedy_metrics['class_level_agreement_mean']:.4f}"
    )
    print(
        f"  6. Latencia media           {latency['mean_ms']:.2f} ms  p99 {latency['p99_ms']:.2f} ms"
    )
    print(
        f"  7. Exactitud cruda          modelo {model_metrics['raw_assignment_accuracy']:.4f}   "
        f"greedy {greedy_metrics['raw_assignment_accuracy']:.4f}"
    )
    print(f"Métricas en {out}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("xgb", "lightgbm", "attention", "all"), default="all")
    parser.add_argument(
        "--episodes-dir", type=Path, default=DEFAULT_EPISODES_DIR / "extrap_5_6_same"
    )
    parser.add_argument("--policy", default=None)
    args = parser.parse_args()

    names = ["xgboost", "lightgbm", "attention"] if args.model == "all" else [args.model]
    if names == ["xgb"]:
        names = ["xgboost"]
    for name in names:
        evaluate_model_on(name, args.episodes_dir, args.policy)


if __name__ == "__main__":
    main()
