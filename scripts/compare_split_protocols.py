"""A/B honesto: mismos datos, mismos hiperparámetros, distinto protocolo.

Entrena XGBoost dos veces sobre el mismo dataset. La única diferencia es cómo
se parte: GroupShuffleSplit aleatorio (el protocolo viejo del pipeline Kedro)
frente al holdout temporal (el protocolo unificado). Cuantifica cuánto de la
métrica publicada venía de la fuga.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve()
while not (REPO / "pyproject.toml").exists():
    REPO = REPO.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "fleet_loading" / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fleet_loading.pipelines.training.pairwise import (  # noqa: E402
    build_tensors,
    derive_classes,
    evaluate_split,
    logits_from_proba,
    option_rows,
    stack_episode_logits,
)
from sklearn.model_selection import GroupShuffleSplit  # noqa: E402

from src.modeling.protocol import SplitConfig, make_splits  # noqa: E402

HIPER = dict(
    max_depth=5,
    learning_rate=0.1,
    n_estimators=150,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    scale_pos_weight=200,
    n_jobs=-1,
    tree_method="hist",
    eval_metric="logloss",
)


def cargar() -> pd.DataFrame:
    keep = ["episode_id", "iso_year", "truck_capacities", "n_loaded", "cu_utilized", "optimal"]
    eps = pd.read_parquet(REPO / "data/episodes/episodes.parquet")
    veh = pd.read_parquet(REPO / "data/episodes/episode_vehicles.parquet")
    return veh.merge(eps[keep], on="episode_id", how="inner", validate="many_to_one")


def particion_aleatoria(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df[df["optimal"].astype(bool)].reset_index(drop=True)
    eps = df[["episode_id"]].drop_duplicates()
    tr, va = next(
        GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(
            eps, groups=eps["episode_id"]
        )
    )
    val_ids = set(eps.iloc[va]["episode_id"])
    return (
        df[~df["episode_id"].isin(val_ids)].reset_index(drop=True),
        df[df["episode_id"].isin(val_ids)].reset_index(drop=True),
    )


def correr(nombre: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> dict:
    import xgboost as xgb

    classes = derive_classes(train_df)
    tr_eps, tr_arr, scaler = build_tensors(train_df, classes)
    max_t = max(tr_arr.max_trucks, max(e.n_trucks for e in tr_eps))
    va_eps, va_arr, _ = build_tensors(val_df, classes, scaler, max_trucks=max_t)

    x_tr, y_tr = option_rows(tr_eps, scaler)
    print(f"  [{nombre}] filas de opción train={len(x_tr):,}", flush=True)

    model = xgb.XGBClassifier(**HIPER)
    model.fit(x_tr, y_tr, verbose=False)

    def proba(x):
        return np.asarray(model.predict_proba(x))

    logits = stack_episode_logits(
        va_eps, va_arr, {i: logits_from_proba(ep, scaler, proba) for i, ep in enumerate(va_eps)}
    )
    m, g = evaluate_split(va_eps, va_arr, logits, classes, policy="count")
    return {
        "protocolo": nombre,
        "episodios_val": m["n_episodes"],
        "exactitud_cruda": m["raw_assignment_accuracy"],
        "iguala_al_maestro_%": m["episodes_matching_teacher_count_pct"],
        "brecha_conteo": m["loaded_gap_mean"],
        "f1_macro": m["macro_f1"],
        "violacion_capacidad": m["capacity_violation_rate"],
        "greedy_iguala_%": g["episodes_matching_teacher_count_pct"],
    }


def main() -> None:
    df = cargar()
    filas = []

    print("== Protocolo VIEJO: GroupShuffleSplit aleatorio ==", flush=True)
    filas.append(correr("aleatorio (viejo)", *particion_aleatoria(df)))

    print("== Protocolo NUEVO: holdout temporal ==", flush=True)
    b = make_splits(df, SplitConfig())
    filas.append(correr("temporal (nuevo)", b["train"], b["val"]))

    out = pd.DataFrame(filas).set_index("protocolo").T
    print("\n" + "=" * 78)
    print("XGBoost, mismos hiperparámetros, misma semilla. Solo cambia la partición.")
    print("=" * 78)
    print(out.to_string(float_format=lambda v: f"{v:,.4f}"))


if __name__ == "__main__":
    main()
