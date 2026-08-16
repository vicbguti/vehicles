#!/usr/bin/env python3
"""Genera un manifiesto CSV de prueba para el API, muestreando vehículos reales.

Los vehículos salen de ``data/episodes/episode_vehicles.parquet`` (los mismos
que se usan para entrenar y evaluar): uids, clases y CU reales, así que el CSV
siempre cae dentro de la distribución que los modelos vieron. La flota sale de
``src.loading.scenarios.make_fleet``, el mismo código del conjunto de
extrapolación (``scripts/build_extrapolation_set.py``).

De dónde vienen los "instancias pequeñas"
------------------------------------------
Un episodio es un (año, semana, cantón) del SRI. El generador de escenarios
submuestrea cada semana a 5-20 vehículos (``FLOOR_N``/``MAX_N`` en
``src/loading/scenarios.py``) porque ese es el presupuesto del maestro exacto.
Así que:

* ``--vehicles 5..20`` -- el manifiesto es UN episodio real completo (misma
  semana y cantón), el mismo tipo de instancia que vio el entrenamiento.
* ``--vehicles < 5``  -- por debajo del piso no existen episodios reales; se
  muestrean filas sueltas (útil para probar el manejo de manifiestos chicos).
* ``--vehicles > 20`` -- una semana real en los archivos limpios tiene cientos
  de vehículos, no 20; el generador mezcla varios episodios. El modelo pairwise
  los atiende igual: el eje de vehículos nunca está acotado.

Los camiones aceptan **cualquier** número (el objetivo de extrapolación a
flotas mayores): ``same`` replica la distribución de capacidad del
entrenamiento, ``constant-total`` mantiene la misma capacidad total que una
flota de 4. Con más de 4 camiones sólo los modelos pairwise los sirven (RF y
logreg responden 422 con su tope).

Cada corrida anota su procedencia: el script imprime (o escribe junto al CSV,
si ``--out`` se da) un ``.provenance.json`` con la fuente, los episodios y las
semillas usadas, para que un manifiesto de prueba sea reproducible y
rastreable.

Uso (desde la raíz del repositorio)::

    fleet_loading/.venv/bin/python scripts/sample_manifest.py --trucks 4
    fleet_loading/.venv/bin/python scripts/sample_manifest.py \\
        --vehicles 8 --trucks 6 --cap-mode constant-total
    fleet_loading/.venv/bin/python scripts/sample_manifest.py \\
        --vehicles 300 --trucks 10 --out data/examples/manifiesto_10.csv
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402

from src.loading.scenarios import FLOOR_N, MAX_N, make_fleet  # noqa: E402

DEFAULT_EPISODES_DIR = REPO_ROOT / "data" / "episodes"
DEFAULT_VEHICLES = 12


def pick_episode(vehicles: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Un episodio real completo con `n` vehículos (o el más cercano)."""
    sizes = vehicles.groupby("episode_id")["uid"].size()
    target = sizes.sub(n).abs().idxmin()
    return vehicles[vehicles["episode_id"] == target]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-dir", type=Path, default=DEFAULT_EPISODES_DIR)
    parser.add_argument(
        "--vehicles",
        type=int,
        default=DEFAULT_VEHICLES,
        help=(
            f"Número de vehículos. {FLOOR_N}-{MAX_N}: un episodio real completo; "
            "por debajo o por encima, muestra de filas/mezcla de episodios."
        ),
    )
    parser.add_argument(
        "--trucks",
        type=int,
        default=2,
        help="Número de camiones. Cualquier valor >= 1; > 4 es extrapolación.",
    )
    parser.add_argument(
        "--cap-mode",
        choices=("same", "constant-total"),
        default="same",
        help=(
            "same: capacidades uniformes (3, 9) como en entrenamiento. "
            "constant-total: misma capacidad total que una flota de 4, repartida "
            "entre más camiones (escenario difícil)."
        ),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta del CSV; sin él, el CSV sale por stdout y la procedencia por stderr.",
    )
    parser.add_argument("--no-provenance", action="store_true")
    args = parser.parse_args()

    if args.vehicles < 1:
        raise SystemExit("--vehicles debe ser >= 1")
    if args.trucks < 1:
        raise SystemExit("--trucks debe ser >= 1")

    episodes_dir = args.episodes_dir
    vehicles = pd.read_parquet(episodes_dir / "episode_vehicles.parquet")

    if FLOOR_N <= args.vehicles <= MAX_N:
        sample = pick_episode(vehicles, args.vehicles, args.seed)
        origin = {
            "mode": "episodio_real_completo",
            "episode_ids": sample["episode_id"].unique().tolist(),
        }
    else:
        sample = vehicles.sample(n=args.vehicles, random_state=args.seed)
        origin = {
            "mode": "muestra_de_filas" if args.vehicles < FLOOR_N else "mezcla_de_episodios",
            "episode_ids": sample["episode_id"].unique().tolist(),
        }

    fleet = make_fleet(random.Random(args.seed), args.trucks, args.cap_mode)
    total_capacity = round(sum(fleet), 2)
    total_cu = round(float(sample["cu"].sum()), 2)

    manifest = sample[["uid", "clase", "cu", "canton"]].copy()
    manifest = manifest.rename(columns={"uid": "identificador"})

    csv_text = manifest.to_csv(index=False, sep=";", lineterminator="\n")

    provenance = {
        "generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "seed": args.seed,
        "source": {
            "vehicles": str(episodes_dir / "episode_vehicles.parquet"),
            "n_source_rows": len(vehicles),
            "n_source_episodes": vehicles["episode_id"].nunique(),
            "n_episodes_usadas": sample["episode_id"].nunique(),
            "origin": origin,
            "iso_years": sorted(sample["episode_id"].str[:4].unique().tolist()),
            "cantons": sorted(sample["canton"].unique().tolist()),
        },
        "manifest": {
            "n_vehicles": len(manifest),
            "n_trucks": args.trucks,
            "cap_mode": args.cap_mode,
            "fleet": fleet,
            "total_capacity": total_capacity,
            "total_cu": total_cu,
            "capacity_utilization": round(total_cu / total_capacity, 3),
            "class_proportions": {
                str(k): round(v, 3)
                for k, v in (sample["clase"].value_counts(normalize=True).items())
            },
        },
        "notes": [
            f"Un episodio real es un (año, semana, cantón) submuestreado a "
            f"{FLOOR_N}-{MAX_N} vehículos (FLOOR_N/MAX_N).",
            "Por encima de 20 vehículos no existe un único episodio real en el "
            "archivo de episodios: es una mezcla de episodios (una semana real "
            "en los archivos limpios tiene cientos de vehículos).",
            f"Con {args.trucks} camiones "
            f"({'más de 4: extrapolación' if args.trucks > 4 else 'dentro del rango'}), "
            "solo los modelos pairwise (xgboost, lightgbm, attention, mlp) lo sirven "
            "sin tope; rf y logreg responden 422 por encima de 4 camiones.",
        ],
    }

    if args.out:
        out = args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(csv_text, encoding="utf-8")
        if not args.no_provenance:
            (out.with_suffix(out.suffix + ".provenance.json")).write_text(
                json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(f"Manifiesto: {out} ({len(manifest)} vehículos, {args.trucks} camiones)")
        print(f"Procedencia: {out}.provenance.json")
    else:
        sys.stdout.write(csv_text)
        if not args.no_provenance:
            sys.stderr.write(
                json.dumps(provenance, indent=2, ensure_ascii=False) + "\n"
            )


if __name__ == "__main__":
    main()
