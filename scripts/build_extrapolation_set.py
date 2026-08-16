#!/usr/bin/env python3
"""Genera conjuntos de prueba FUERA del sobre de entrenamiento, en dos ejes.

El generador de episodios encierra cada episodio en un sobre estrecho:
`N_TRUCKS_RANGE = (1, 4)` camiones y `MAX_N = 20` vehículos. La arquitectura por
pares **puede** atender cualquier tamaño con los mismos pesos, pero eso es una
propiedad del diseño, no un resultado medido. Este script produce la evidencia,
cambiando **una sola variable por conjunto**:

`--axis trucks` -- *cuántos camiones*.
    Toma los manifiestos que el modelo ya iba a evaluar (mismos vehículos, mismas
    clases, mismos CU), les cambia sólo la flota y los reetiqueta con el maestro
    exacto `src/loading/labeler.assign_vehicles`.

`--axis manifest` -- *cuántos vehículos*.
    No puede reutilizar `episode_vehicles.parquet`: esos manifiestos **ya vienen
    recortados a 20**. Vuelve a `data/features/vehicles_in_scope.parquet`, reagrupa
    por (año, semana, cantón) y submuestrea a un `--max-n` mayor. Importa porque el
    recorte no es marginal: el 51 % de los grupos cantón-semana reales supera los 20
    vehículos (mediana 21, máximo 2.774) y el modelo nunca vio uno mayor.

Ninguno de los dos toca el conjunto de **entrenamiento**: `--years` restringe la
construcción al año de prueba, y `MAX_N` sigue siendo el valor por omisión en todo
lo demás.

El maestro es exacto sólo mientras certifique optimalidad dentro de su presupuesto.
Por eso ambos ejes guardan `optimal`, `search_time_ms` y `nodes_explored`, y el
resumen imprime la tasa de certificación: hasta dónde llega el maestro es, en sí
mismo, uno de los resultados que el conjunto debe medir.

Uso (desde la raíz del repositorio):
    uv run python scripts/build_extrapolation_set.py --n-trucks 5 6
    uv run python scripts/build_extrapolation_set.py --n-trucks 8 10 --cap-mode constant-total
    uv run python scripts/build_extrapolation_set.py --axis manifest --max-n 40
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402

from src.loading.labeler import Vehicle, assign_vehicles  # noqa: E402
from src.loading.scenarios import (  # noqa: E402
    FLOOR_N,
    MAX_N,
    build_all_episodes,
    make_fleet,
)

DEFAULT_EPISODES_DIR = REPO_ROOT / "data" / "episodes"
DEFAULT_FEATURES_PATH = REPO_ROOT / "data" / "features" / "vehicles_in_scope.parquet"


def extrapolation_seed(episode_id: str, n_trucks: int) -> int:
    """Semilla estable e independiente de PYTHONHASHSEED, como en scenarios.py."""
    key = f"extrapolation:{episode_id}:{n_trucks}"
    return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)


def build_truck_axis(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mismos manifiestos, flota mayor. Reetiqueta con el maestro exacto."""
    episodes = pd.read_parquet(args.episodes_dir / "episodes.parquet")
    vehicles = pd.read_parquet(args.episodes_dir / "episode_vehicles.parquet")

    keep = episodes[episodes["iso_year"].isin(args.years)]
    if args.limit:
        keep = keep.head(args.limit)
    vehicles = vehicles[vehicles["episode_id"].isin(set(keep["episode_id"]))]

    episode_records, vehicle_records = [], []
    meta = keep.set_index("episode_id")

    for episode_id, group in vehicles.groupby("episode_id", sort=True):
        rng = random.Random(extrapolation_seed(episode_id, args.n_trucks[0]))
        n_trucks = rng.choice(args.n_trucks)
        fleet = make_fleet(rng, n_trucks, args.cap_mode)

        veh = [Vehicle(uid=r.uid, clase=r.clase, cu=r.cu) for r in group.itertuples()]
        result = assign_vehicles(
            veh, fleet, time_budget_s=args.time_budget, seed=rng.randrange(2**31)
        )

        row = meta.loc[episode_id]
        episode_records.append(
            {
                "episode_id": episode_id,
                "iso_year": int(row["iso_year"]),
                "iso_week": int(row["iso_week"]),
                "canton": int(row["canton"]),
                "n_sampled": len(group),
                "n_trucks": len(fleet),
                "truck_capacities": fleet,
                "n_loaded": result.n_loaded,
                "n_deferred": result.n_deferred,
                "cu_utilized": result.cu_utilized,
                "optimal": result.optimal,
                # El coste del maestro es parte del resultado, no telemetría: dice
                # hasta dónde sigue habiendo un óptimo certificado contra el que medir.
                "search_time_ms": result.search_time_ms,
                "nodes_explored": result.nodes_explored,
            }
        )
        for r in group.itertuples():
            truck = result.assignment[r.uid]
            vehicle_records.append(
                {
                    "episode_id": episode_id,
                    "uid": r.uid,
                    "clase": r.clase,
                    "cu": r.cu,
                    "canton": r.canton,
                    "truck": truck,
                    "loaded": truck != "SIN_CAMION",
                }
            )

    return pd.DataFrame(episode_records), pd.DataFrame(vehicle_records)


def build_manifest_axis(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Manifiestos mayores, misma distribución de flota.

    Delega en `build_all_episodes`, que es exactamente el constructor del conjunto
    de entrenamiento con un único parámetro cambiado. Reimplementarlo aquí sería
    volver a escribir el piso `FLOOR_N`, el submuestreo estratificado, la flota
    ordenada y la semilla estable por episodio -- y arriesgarse a que divergieran.
    """
    features = pd.read_parquet(args.features_path)
    features = features[features["iso_year"].isin(args.years)]
    episodes, vehicles, summary = build_all_episodes(
        features, limit=args.limit, time_budget_s=args.time_budget, max_n=args.max_n
    )
    print(
        f"Grupos: {summary.n_groups_total:,}  "
        f"bajo el piso de {FLOOR_N}: {summary.n_below_floor:,}  "
        f"episodios: {summary.n_episodes_built:,}"
    )
    return episodes, vehicles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--axis",
        choices=("trucks", "manifest"),
        default="trucks",
        help="Qué variable sale del sobre de entrenamiento.",
    )
    parser.add_argument("--episodes-dir", type=Path, default=DEFAULT_EPISODES_DIR)
    parser.add_argument("--features-path", type=Path, default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_EPISODES_DIR)
    parser.add_argument("--n-trucks", type=int, nargs="+", help="Sólo para --axis trucks.")
    parser.add_argument("--cap-mode", choices=("same", "constant-total"), default="same")
    parser.add_argument(
        "--max-n",
        type=int,
        help=f"Sólo para --axis manifest. Tope de vehículos por episodio (entrenamiento: {MAX_N}).",
    )
    parser.add_argument("--time-budget", type=float, default=5.0)
    parser.add_argument("--years", type=int, nargs="*", default=[2026])
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.axis == "trucks":
        if not args.n_trucks:
            parser.error("--axis trucks requiere --n-trucks")
        tag = f"extrap_{'_'.join(map(str, args.n_trucks))}_{args.cap_mode.replace('-', '')}"
    else:
        if args.max_n is None:
            parser.error("--axis manifest requiere --max-n")
        if args.max_n <= MAX_N:
            parser.error(f"--max-n debe superar el tope de entrenamiento ({MAX_N}) para extrapolar")
        tag = f"extrap_maxn_{args.max_n}"

    out_dir = args.out_root / tag
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.axis == "trucks":
        ep_df, ve_df = build_truck_axis(args)
        print(f"Eje: camiones {sorted(args.n_trucks)}  modo de capacidad: {args.cap_mode}")
    else:
        ep_df, ve_df = build_manifest_axis(args)
        print(f"Eje: tamaño de manifiesto  max_n: {args.max_n} (entrenamiento: {MAX_N})")

    ep_df.to_parquet(out_dir / "episodes.parquet", index=False)
    ve_df.to_parquet(out_dir / "episode_vehicles.parquet", index=False)

    non_optimal = int((~ep_df["optimal"]).sum())
    tiempos = ep_df["search_time_ms"]
    print(f"Episodios: {len(ep_df):,}  filas: {len(ve_df):,}")
    print(
        f"Vehículos por episodio: media {ep_df['n_sampled'].mean():.1f}  "
        f"máx {ep_df['n_sampled'].max()}"
    )
    print(f"Capacidad total media: {ep_df['truck_capacities'].apply(sum).mean():.2f} CU")
    print(
        f"Diferidos: {int(ep_df['n_deferred'].sum()):,} "
        f"({100 * (~ve_df['loaded']).mean():.2f}% de las filas)"
    )
    # Sin optimalidad certificada no hay óptimo contra el que medir la brecha, y
    # `dataset.drop_non_optimal` descarta esos episodios en la evaluación.
    print(
        f"Maestro: certifica el {100 * (1 - non_optimal / len(ep_df)):.2f}% "
        f"({non_optimal} sin certificar de {len(ep_df):,}), "
        f"búsqueda media {tiempos.mean():.1f} ms  p99 {tiempos.quantile(0.99):.1f} ms"
    )
    print(f"Escrito en {out_dir}")


if __name__ == "__main__":
    main()
