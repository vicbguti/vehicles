#!/usr/bin/env python3
"""Entrena RandomForest o regresión logística multinomial (índice canónico fijo).

    data/episodes/episodes.parquet + episode_vehicles.parquet
            -> join, descarte de episodios no-óptimos, partición temporal
            -> canonicalización de la flota por capacidad (src.modeling.features)
            -> una fila por vehículo, flota rellenada a --max-trucks (src.modeling.flat_features)
            -> búsqueda de hiperparámetros con Optuna, cada intento logueado a MLflow
            -> mejor modelo: métricas de dominio (src.modeling.metrics) + artifacts/<model>/

A diferencia del MLP y las GBTs de `fleet_loading` (eje de camiones dinámico,
`(V, T, 19)`), este script entrena un clasificador multiclase estándar de
scikit-learn: la flota se rellena a un tamaño fijo y el modelo predice
directamente el índice canónico (`0 = SIN_CAMION`, `1..max_trucks` el camión).
Es la formulación que corresponde a "regresión logística multinomial" en
sentido estricto (softmax sobre clases fijas) y al uso nativo de
`RandomForestClassifier`. Ver `src/modeling/flat_features.py` para el porqué.

Uso (desde la raíz del repositorio):
    uv run python scripts/train_classical.py --model rf
    uv run python scripts/train_classical.py --model logreg --n-trials 100
    uv run python scripts/train_classical.py --model rf --tracking-uri sqlite:////content/drive/MyDrive/vehicles-mlflow/mlflow.db

En Colab: montar Drive, clonar el repo, `pip install -q scikit-learn optuna
mlflow pyarrow`, y pasar `--tracking-uri` apuntando a un archivo dentro de
Drive para que el tracking persista entre sesiones.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402

from src.modeling.capacity_decoder import POLICIES, decode_episode  # noqa: E402
from src.modeling.dataset import (  # noqa: E402
    assert_no_episode_leakage,
    drop_non_optimal,
    load_episode_tables,
    split_by_episode_hash,
    split_by_time,
    summarize_splits,
)
from src.modeling.features import BlockScaler, build_all_episodes  # noqa: E402
from src.modeling.flat_features import (  # noqa: E402
    FlatArrays,
    build_flat_arrays,
    flat_feature_names,
)
from src.modeling.metrics import (  # noqa: E402
    aggregate,
    build_result,
    episode_logits,
    evaluate_greedy,
)
from src.pipeline.transformation.derived_fields import VehicleClassConfig  # noqa: E402

DEFAULT_EPISODES_DIR = REPO_ROOT / "data" / "episodes"
CLASS_CONFIG_PATH = REPO_ROOT / "config" / "vehicle_classes.yaml"
DEFAULT_TRACKING_URI = f"sqlite:///{REPO_ROOT / 'mlflow.db'}"

MODEL_NAMES = ("rf", "logreg")

# Hiperparámetros que no se buscan -- se fijan por conocimiento del dominio
# (desbalance de clases documentado en docs/decisiones/01_hallazgos_transversales.md
# punto 5) o por estabilidad numérica, y se aplican tanto en cada intento de
# Optuna como en el reentrenamiento final del mejor trial.
RF_FIXED = dict(class_weight="balanced", n_jobs=-1, random_state=42)
LOGREG_FIXED = dict(max_iter=2000, random_state=42)


# ------------------------------------------------------------------ búsqueda
def suggest_rf_params(trial) -> dict:
    return dict(
        n_estimators=trial.suggest_int("n_estimators", 100, 800, step=50),
        max_depth=trial.suggest_int("max_depth", 4, 30),
        min_samples_split=trial.suggest_int("min_samples_split", 2, 20),
        min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
        max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    )


def suggest_logreg_params(trial) -> dict:
    solver = trial.suggest_categorical("solver", ["lbfgs", "saga"])
    # lbfgs sólo admite L2 puro (l1_ratio=0); saga admite el rango completo
    # [0, 1] (0=L2, 1=L1, intermedio=elastic-net) -- búsqueda condicional.
    # `penalty` (l1/l2 como string) está deprecado desde sklearn 1.8 a favor de
    # `l1_ratio`: pasar penalty="l1" con el l1_ratio=0.0 por defecto produce un
    # UserWarning de "Inconsistent values" y NO aplica L1 -- se detectó al
    # correr el smoke test contra sklearn 1.9. `l1_ratio` es la API vigente.
    l1_ratio = trial.suggest_float("l1_ratio", 0.0, 1.0) if solver == "saga" else 0.0
    return dict(
        C=trial.suggest_float("C", 1e-4, 1e2, log=True),
        solver=solver,
        l1_ratio=l1_ratio,
        class_weight=trial.suggest_categorical("class_weight", ["balanced", None]),
        # sklearn >=1.5 usa pérdida multinomial (softmax) por defecto con estos
        # solvers cuando hay más de 2 clases -- el flag explícito
        # `multi_class="multinomial"` está deprecado (eliminado en 1.7), así
        # que no se pasa.
    )


def suggest_params(model_name: str, trial) -> dict:
    return suggest_rf_params(trial) if model_name == "rf" else suggest_logreg_params(trial)


def fixed_extras(model_name: str) -> dict:
    return dict(RF_FIXED) if model_name == "rf" else dict(LOGREG_FIXED)


def finalize_params(model_name: str, best_params: dict) -> dict:
    """Reconstruye los hiperparámetros completos del trial ganador.

    `study.best_params` sólo trae las claves que Optuna efectivamente sugirió
    en ESE trial -- si ganó `solver="lbfgs"`, la clave `"l1_ratio"` nunca se
    sugirió (es condicional a `solver="saga"` en `suggest_logreg_params`) y no
    aparece. Se completa aquí con el mismo default, en vez de reproducir la
    búsqueda con un trial ficticio.
    """
    params = dict(best_params)
    if model_name == "logreg" and "l1_ratio" not in params:
        params["l1_ratio"] = 0.0
    return {**params, **fixed_extras(model_name)}


def build_model(model_name: str, params: dict):
    if model_name == "rf":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(**params)
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(**params)


# ------------------------------------------------------------- métricas de dominio
def domain_metrics_for_split(
    model, episodes: list, flat: FlatArrays, n_classes: int, policy: str
) -> dict:
    """Decodifica las probabilidades del modelo y agrega con `src.modeling.metrics`.

    `flat` ya expone `episode_index`/`target` con la firma que espera las
    funciones de `src.modeling.metrics`, así que las métricas de dominio
    (violación de capacidad, brecha de vehículos cargados, F1 macro, matriz de
    confusión, ...) se calculan con el mismo código que usan el MLP y las
    GBTs -- no hay una segunda implementación de las métricas para este modelo.
    """
    logits = model.predict_proba(flat.X)  # (N, 1 + max_trucks), orden canónico
    max_labels = logits.shape[1]

    results = []
    for ep_i, ep in enumerate(episodes):
        rows = np.flatnonzero(flat.episode_index == ep_i)
        decoded = decode_episode(
            episode_logits(logits, rows, ep.n_trucks),
            cu=ep.cu,
            capacities=ep.capacities,
            policy=policy,
        )
        results.append(build_result(ep, decoded, flat.target[rows], n_classes))
    return aggregate(results, max_labels)


def select_policy(model, episodes: list, flat: FlatArrays, n_classes: int) -> str:
    """Elige la política del decodificador por validación (brecha de carga mínima)."""
    best, best_gap = "count", float("inf")
    for policy in POLICIES:
        m = domain_metrics_for_split(model, episodes, flat, n_classes, policy)
        if m["loaded_gap_mean"] < best_gap:
            best, best_gap = policy, m["loaded_gap_mean"]
    return best


# ---------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_NAMES, required=True)
    parser.add_argument("--episodes-dir", type=Path, default=DEFAULT_EPISODES_DIR)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--split", choices=("time", "hash"), default="time")
    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Paralelismo de Optuna entre intentos (no confundir con el n_jobs=-1 "
        "interno de RandomForest). Default 1 para no sobre-suscribir CPUs: cada "
        "árbol ya usa todos los cores. Súbelo sólo para logreg, que no paraleliza "
        "internamente.",
    )
    parser.add_argument("--tracking-uri", default=DEFAULT_TRACKING_URI)
    parser.add_argument("--experiment-name", default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = args.out_dir or (REPO_ROOT / "artifacts" / args.model)
    out_dir.mkdir(parents=True, exist_ok=True)
    experiment_name = args.experiment_name or f"vehicles-{args.model}"

    import mlflow
    import mlflow.sklearn
    import optuna

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(experiment_name)

    # --- Datos ---------------------------------------------------------------
    joined = load_episode_tables(
        args.episodes_dir / "episodes.parquet",
        args.episodes_dir / "episode_vehicles.parquet",
    )
    joined, n_non_optimal = drop_non_optimal(joined)

    splits = split_by_time(joined) if args.split == "time" else split_by_episode_hash(joined)
    assert_no_episode_leakage(splits)
    summaries = summarize_splits(splits)
    for s in summaries:
        if s.n_rows == 0:
            raise SystemExit(
                f"La partición '{s.name}' quedó vacía. Con la muestra de humo use "
                "--split hash: los 200 episodios caen todos en 2018-W02."
            )

    classes = sorted(VehicleClassConfig.from_yaml(str(CLASS_CONFIG_PATH)).in_scope_classes)
    episodes = {name: build_all_episodes(df, classes) for name, df in splits.items()}

    max_trucks = max(e.n_trucks for eps in episodes.values() for e in eps)
    n_classes = len(classes)
    n_labels = max_trucks + 1

    scaler = BlockScaler.fit(episodes["train"], classes)
    flat = {name: build_flat_arrays(eps, scaler, max_trucks) for name, eps in episodes.items()}
    feat_names = flat_feature_names(classes, max_trucks)

    print(f"Modelo: {args.model}   Clases: {classes}   Camiones máximos: {max_trucks}")
    for s in summaries:
        print(
            f"  {s.name:<5} episodios={s.n_episodes:>7,}  filas={s.n_rows:>8,}  "
            f"diferidos={s.n_deferred_rows:>7,} ({s.deferred_pct:.2f}%)  años={list(s.years)}"
        )

    # --- Búsqueda de hiperparámetros ------------------------------------------
    train, val = flat["train"], flat["val"]

    def objective(trial: optuna.Trial) -> float:
        from sklearn.metrics import accuracy_score, f1_score

        params = {**suggest_params(args.model, trial), **fixed_extras(args.model)}
        with mlflow.start_run(run_name=f"{args.model}_trial_{trial.number}", nested=True):
            mlflow.log_params(params)
            model = build_model(args.model, params).fit(train.X, train.target)
            pred = model.predict(val.X)
            val_accuracy = accuracy_score(val.target, pred)
            val_macro_f1 = f1_score(val.target, pred, average="macro", zero_division=0)
            mlflow.log_metrics({"val_raw_accuracy": val_accuracy, "val_macro_f1": val_macro_f1})
        return val_macro_f1

    t0 = time.perf_counter()
    with mlflow.start_run(run_name=f"{args.model}_search") as parent_run:
        mlflow.log_params(
            {
                "model": args.model,
                "n_trials": args.n_trials,
                "split_strategy": args.split,
                "max_trucks": max_trucks,
                "n_features": len(feat_names),
                "seed": args.seed,
            }
        )
        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=args.seed),
        )
        study.optimize(objective, n_trials=args.n_trials, n_jobs=args.n_jobs)
        search_seconds = time.perf_counter() - t0

        best_params = finalize_params(args.model, study.best_params)
        best_model = build_model(args.model, best_params).fit(train.X, train.target)

        # `predict_proba` sólo devuelve columnas para las clases vistas en
        # `train.target` (`model.classes_`). Si alguna vez faltara una -- p.ej.
        # ningún vehículo fue al camión más chico de una flota de 4 en todo
        # train --, las columnas de `predict_proba` quedarían desalineadas con
        # el índice canónico que espera `decode_episode` (columna `j` = camión
        # `j`). Se falla ruidosamente en vez de decodificar mal en silencio.
        expected_classes = np.arange(n_labels)
        if not np.array_equal(best_model.classes_, expected_classes):
            raise SystemExit(
                f"El mejor modelo sólo vio las clases {best_model.classes_.tolist()} en "
                f"entrenamiento, se esperaban {expected_classes.tolist()}. Revisar el "
                "balance de clases de la partición 'train'."
            )

        policy = select_policy(best_model, episodes["val"], val, n_classes)
        domain = {
            name: domain_metrics_for_split(
                best_model, episodes[name], flat[name], n_classes, policy
            )
            for name in ("train", "val", "test")
        }
        greedy_val = aggregate(evaluate_greedy(episodes["val"], val, n_classes), n_labels)

        mlflow.log_params({"best_" + k: v for k, v in study.best_params.items()})
        mlflow.log_param("decoder_policy", policy)
        mlflow.log_metrics(
            {
                f"{name}_{metric}": value
                for name, m in domain.items()
                for metric, value in m.items()
                if isinstance(value, (int, float))
            }
        )
        mlflow.sklearn.log_model(best_model, "model")
        best_run_id = parent_run.info.run_id

    # --- Artefactos ------------------------------------------------------------
    import joblib

    joblib.dump(best_model, out_dir / "model.joblib")

    (out_dir / "feature_schema.json").write_text(
        json.dumps(
            {
                "model": args.model,
                "classes": classes,
                "max_trucks_padding": max_trucks,
                "feature_names": feat_names,
                "blocks": scaler.to_dict(),
                "decoder_policy": policy,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (out_dir / "label_mapping.json").write_text(
        json.dumps(
            {
                "0": "SIN_CAMION",
                **{str(i + 1): f"CAMION_{i + 1}" for i in range(max_trucks)},
                "_nota": (
                    "Índices canónicos: CAMION_1 es el camión de MAYOR capacidad del "
                    "episodio. Ver src/modeling/canonicalization.py."
                ),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    label_counts = {
        name: {
            str(k): int(v) for k, v in zip(*np.unique(a.target, return_counts=True), strict=True)
        }
        for name, a in flat.items()
    }
    (out_dir / "training_report.json").write_text(
        json.dumps(
            {
                "generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                "model": args.model,
                "episodes_dir": str(args.episodes_dir),
                "split_strategy": args.split,
                "episodes_dropped_non_optimal": n_non_optimal,
                "splits": [s.as_dict() for s in summaries],
                "canonical_label_counts": label_counts,
                "n_trials": args.n_trials,
                "best_params": study.best_params,
                "best_val_macro_f1": study.best_value,
                "decoder_policy": policy,
                "domain_metrics": domain,
                "greedy_baseline_val": greedy_val,
                "search_seconds": round(search_seconds, 1),
                "mlflow_tracking_uri": args.tracking_uri,
                "mlflow_experiment": experiment_name,
                "mlflow_run_id": best_run_id,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\nBúsqueda: {args.n_trials} intentos en {search_seconds:.1f}s")
    print(f"Mejores hiperparámetros: {study.best_params}")
    print(f"Política de decodificador elegida: {policy}")
    print(
        f"Test  -- capacity_violation_rate={domain['test']['capacity_violation_rate']:.4f}  "
        f"loaded_gap_mean={domain['test']['loaded_gap_mean']:.4f}  "
        f"raw_assignment_accuracy={domain['test']['raw_assignment_accuracy']:.4f}"
    )
    print(f"Artefactos en {out_dir}")
    print(f"MLflow: experimento '{experiment_name}', run {best_run_id} en {args.tracking_uri}")


if __name__ == "__main__":
    main()
