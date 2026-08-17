"""src/api/examples.py

Manifiestos de ejemplo para el API, construidos SIEMPRE con vehículos reales
del SRI (registro ``data/features/vehicles_in_scope.parquet``), que es el
objetivo del proyecto.

El ejemplo del profesor (18 vehículos, 2 clases, 2 camiones de 6 unidades) se
realiza sobre las clases que entrena el proyecto --Sedán -> AUTOMOVIL y
SUV -> JEEP-- con sus CU reales del SRI (1.0 y 1.1). El CSV devuelto es el
mismo que lee ``parse_csv``: los vehículos se modelan con el esquema pydantic
del API y se serializan con cabeceras ``identificador;clase;cu;canton``.

El registro se carga una sola vez y se cachea (como el servicio de modelos);
la flota no va en el CSV, se envía en el cuerpo de ``POST /api/distribute``.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pandas as pd

from src.api.schemas import ManifestVehicleIn
from src.loading.scenarios import CAP_RANGE

REPO_ROOT = Path(__file__).resolve().parents[2]
SRI_REGISTRY = REPO_ROOT / "data" / "features" / "vehicles_in_scope.parquet"

# Ejemplo del profesor: (clase del SRI, cantidad). Sedán -> AUTOMOVIL,
# SUV -> JEEP; los CU son los reales del SRI.
EXAMPLES: dict[str, tuple[list[tuple[str, int]], list[float]]] = {
    "profesor": ([("AUTOMOVIL", 12), ("JEEP", 6)], [6.0, 6.0]),
    "profesor-escalado": ([("AUTOMOVIL", 15), ("JEEP", 10)], [6.0, 7.0, 7.0]),
}

# Un caso-scenario real por defecto: todo lo registrado en el cantón 21701
# durante la semana 9 de 2026 (2,734 vehículos), sin cap de submuestreo.
DEFAULT_REAL_EPISODE = (2026, 9, "21701")

# Fracción del CU del episodio que la flota puede mover: un caso de estrés
# real, no trivial por exceso de espacio ni imposible por falta.
FLEET_CU_FRACTION = 0.95


def _registry() -> pd.DataFrame:
    """Registro real del SRI, cargado una sola vez."""
    if not hasattr(_registry, "_df"):
        _registry._df = pd.read_parquet(SRI_REGISTRY)
    return _registry._df


def _class_seed(seed: int, clase: str) -> int:
    """Semilla estable por clase, independiente de PYTHONHASHSEED (como scenarios.py)."""
    key = f"manifiesto:{seed}:{clase}"
    return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)


def _episode_seed(iso_year: int, iso_week: int, canton: str) -> int:
    """Semilla estable del episodio, para que su flota sea reproducible."""
    key = f"episodio:{iso_year}:{iso_week}:{canton}"
    return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)


def example_fleet(name: str) -> list[float]:
    """La flota declarada del ejemplo (la del enunciado, p. ej. ``[6, 6]``)."""
    if name not in EXAMPLES:
        raise KeyError(name)
    return list(EXAMPLES[name][1])


def example_count(name: str) -> int:
    if name not in EXAMPLES:
        raise KeyError(name)
    return sum(n for _clase, n in EXAMPLES[name][0])


def real_episode_fleet(iso_year: int, iso_week: int, canton: str) -> list[float]:
    """Flota coherente para un episodio real, dimensionada al CU real del
    episodio y determinista por episodio.

    El SRI no publica la flota de transporte --esa es la decisión del
    operador--, así que se construye con la misma convención del entrenamiento
    (cada camión transporta 3-9 CU), pero **escalada al episodio**: el total de
    la flota cubre el ``FLEET_CU_FRACTION`` del CU del episodio, para que el
    caso sea un estrés real (no trivial por exceso de espacio, ni imposible por
    falta). La banda de 1-4 camiones del entrenamiento es para episodios de
    <= 20 vehículos; un cantón completo de cientos de vehículos requiere una
    flota proporcional.
    """
    registry = _registry()
    episode = registry[
        (registry["iso_year"] == iso_year)
        & (registry["iso_week"] == iso_week)
        & (registry["canton"].astype(str) == canton)
    ]
    total_cu = float(episode["cu"].sum())
    target = round(total_cu * FLEET_CU_FRACTION, 1)

    rng = random.Random(_episode_seed(iso_year, iso_week, canton))
    mid_capacity = (CAP_RANGE[0] + CAP_RANGE[1]) / 2
    n_trucks = max(1, round(target / mid_capacity))
    caps = [round(rng.uniform(*CAP_RANGE), 1) for _ in range(n_trucks)]
    scale = target / sum(caps)
    caps = [round(c * scale, 1) for c in caps]
    # Corrige el redondeo para que la flota sume exactamente `target`.
    caps[-1] = round(target - sum(caps[:-1]), 1)
    if caps[-1] <= 0:
        caps[-1] = min(CAP_RANGE)  # un camión mínimo conserva el objetivo
    return sorted(caps)


def real_episode_count(iso_year: int, iso_week: int, canton: str) -> int:
    registry = _registry()
    return int(
        registry[
            (registry["iso_year"] == iso_year)
            & (registry["iso_week"] == iso_week)
            & (registry["canton"].astype(str) == canton)
        ].shape[0]
    )


def build_example_csv(name: str, seed: int = 42) -> str:
    """CSV (punto y coma) del manifiesto de ejemplo, con vehículos reales del SRI."""
    if name not in EXAMPLES:
        raise KeyError(name)
    mix, _fleet = EXAMPLES[name]

    parts = []
    registry = _registry()
    for clase, n in mix:
        pool = registry[registry["clase"] == clase]
        parts.append(pool.sample(n=n, random_state=_class_seed(seed, clase)))

    selected = pd.concat(parts)
    vehicles = [
        ManifestVehicleIn(
            identificador=str(r.codigo_vehiculo),
            clase=r.clase,
            cu=float(r.cu),
            canton=str(r.canton),
        )
        for r in selected.itertuples()
    ]
    return pd.DataFrame([v.model_dump() for v in vehicles]).to_csv(
        index=False, sep=";", lineterminator="\n"
    )


def build_real_episode_csv(iso_year: int, iso_week: int, canton: str) -> str:
    """CSV de un episodio real del SRI: todos los vehículos registrados en
    (año, semana, cantón), SIN cap de submuestreo. Devuelve ``None`` si el
    episodio no existe en el registro.
    """
    registry = _registry()
    episode = registry[
        (registry["iso_year"] == iso_year)
        & (registry["iso_week"] == iso_week)
        & (registry["canton"].astype(str) == canton)
    ]
    if episode.empty:
        return ""
    selected = episode.sort_values(["clase", "codigo_vehiculo"])
    vehicles = [
        ManifestVehicleIn(
            identificador=str(r.codigo_vehiculo),
            clase=r.clase,
            cu=float(r.cu),
            canton=str(r.canton),
        )
        for r in selected.itertuples()
    ]
    return pd.DataFrame([v.model_dump() for v in vehicles]).to_csv(
        index=False, sep=";", lineterminator="\n"
    )
