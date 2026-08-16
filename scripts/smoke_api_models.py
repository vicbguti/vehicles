"""Smoke test de src/api.models contra el venv de fleet_loading.

Verifica que ModelService carga los artefactos y produce un plan factible a
partir de un manifiesto sintético. Uso::

    fleet_loading/.venv/bin/python scripts/smoke_api_models.py [model]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.api.models import ModelService  # noqa: E402

MODELS = {
    "xgboost": "xgb",
    "lightgbm": "lgb",
    "attention": "att",
}

VEHICLES = [
    {"identificador": "2024_124410", "clase": "AUTOMOVIL", "cu": 1.1, "canton": "17001"},
    {"identificador": "2024_120513", "clase": "AUTOMOVIL", "cu": 1.3, "canton": "17001"},
    {"identificador": "2024_118094", "clase": "AUTOMOVIL", "cu": 0.9, "canton": "17001"},
    {"identificador": "2024_116774", "clase": "AUTOMOVIL", "cu": 1.2, "canton": "17001"},
    {"identificador": "2024_115371", "clase": "CAMIONETA", "cu": 1.4, "canton": "17001"},
    {"identificador": "2024_114183", "clase": "AUTOMOVIL", "cu": 1.1, "canton": "17001"},
    {"identificador": "2024_113422", "clase": "MOTOCICLETA", "cu": 0.4, "canton": "17001"},
    {"identificador": "2024_109940", "clase": "JEEP", "cu": 1.2, "canton": "17001"},
    {"identificador": "2024_101771", "clase": "AUTOMOVIL", "cu": 1.0, "canton": "17001"},
]


def main() -> None:
    model_name = sys.argv[1] if len(sys.argv) > 1 else "xgboost"
    service = ModelService(model_name)
    trucks, assignment = service.distribute(VEHICLES, [6.0, 6.0])
    n_loaded = sum(1 for a in assignment if a != -1)
    n_deferred = len(assignment) - n_loaded

    print(f"modelo={model_name} policy={service._policy}")
    print(f"asignación (V={len(VEHICLES)}): {assignment}")
    print(f"cargados={n_loaded} diferidos={n_deferred} camiones={len(trucks)}")
    for t in trucks:
        cu = sum(v["cu"] for v in t["vehicles"])
        ok = cu <= t["capacity"] + 1e-9
        print(
            f"  camion={t['id']} capacidad={t['capacity']} usado={cu:.2f} "
            f"n={len(t['vehicles'])} factible={ok}"
        )
        assert ok, f"viola capacidad en {t['id']}"
    assert n_deferred >= 0
    print("OK")


if __name__ == "__main__":
    main()
