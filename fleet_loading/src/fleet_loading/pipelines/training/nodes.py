from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import mlflow

if TYPE_CHECKING:
    # Solo para la anotación de _confusion_matrix_figure: matplotlib se importa
    # dentro de la función para no cargarlo en cada import del módulo.
    import matplotlib.figure

REPO_ROOT = Path(__file__).resolve().parents[5]
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "fleet_loading"

# Una sola base de MLflow para todo el repositorio. Antes esta ruta subía cuatro
# niveles y no cinco, así que el pipeline escribía en fleet_loading/mlflow.db
# mientras scripts/train_classical.py escribía en la raíz: dos bases, y la UI
# documentada abría solo una. Se usa REPO_ROOT --ya resuelto y absoluto-- en vez
# de contar `..`, que es lo que hizo posible la discrepancia.
MLFLOW_DB = REPO_ROOT / "mlflow.db"
mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB}")

import sys  # noqa: E402

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# E402: estos imports van después del parche de sys.path porque `src.*` no es
# resoluble sin él. El parche desaparece al empaquetar el proyecto.
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score  # noqa: E402

from fleet_loading.pipelines.training.pairwise import (  # noqa: E402
    build_tensors,
    derive_classes,
    evaluate_split,
    logits_from_proba,
    option_rows,
    select_policy,
    stack_episode_logits,
)
from src.modeling.figures import PRESENTACION  # noqa: E402
from src.modeling.metrics import evaluate_model  # noqa: E402
from src.modeling.protocol import SplitConfig, make_splits  # noqa: E402

# Canonical index space (shared with src/modeling): 0 = SIN_CAMION, 1..T = truck
# by capacity descending. No hardcoded truck count: the models are pairwise and
# accept any T.
DEFER_LABEL = 0

# Prefijo de clave -> subdirectorio bajo artifacts/fleet_loading/, que es también
# la clave del registro `PRESENTACION` de src/modeling/figures.py (de donde salen
# los rótulos). Estaba implícito, escrito a mano en cada `_save_model_artifact`.
MODEL_DIRS = {"xgb": "xgboost", "lgb": "lightgbm", "att": "attention"}


def _compute_defer_f1(y_true, y_pred) -> float:
    """F1 for the defer class (canonical index 0) vs everything else."""
    return f1_score(
        (y_true == DEFER_LABEL).astype(int),
        (y_pred == DEFER_LABEL).astype(int),
        zero_division=0,
    )


def _log_gbt_curves(model, metric_name: str, error_metric: str, prefix: str) -> None:
    """Re-log a GBT's train/val curves to MLflow *and* persist them under artifacts/.

    Both XGBoost and LightGBM record per-round eval results in ``evals_result``
    keyed as ``validation_0``/``validation_1`` (XGB) or ``training``/``valid_1``
    (LGB). ``mlflow.autolog`` logs these under those framework names; we re-log
    them as ``<prefix>_train_<metric>`` / ``<prefix>_val_<metric>`` so the MLflow
    UI is unambiguous. Accuracy is logged as ``1 - error`` from the framework's
    error metric.

    MLflow alone was not enough: the tracking DB is gitignored, and when it was
    reset the curves of all three Kedro models ceased to exist -- their run_ids
    no longer resolve. The CSV and PNG go next to the model, which is versioned.
    The step axis here is a **boosting round**, not an epoch; ``write_history``
    records that in the file so no chart can mislabel it.
    """
    result = getattr(model, "evals_result", None)
    result = result() if callable(result) else getattr(model, "_evals_result", None)
    if not result:
        return
    train_series = result.get("validation_0") or result.get("training")
    val_series = result.get("validation_1") or result.get("valid_1") or result.get("valid_0")
    curvas: dict[str, list[float]] = {}
    for name, series in (("train", train_series), ("val", val_series)):
        if not series:
            continue
        loss = series.get(metric_name) or next(iter(series.values()))
        for step, v in enumerate(loss):
            mlflow.log_metric(f"{prefix}_{name}_{metric_name}", v, step=step)
        curvas["loss" if name == "train" else "val_loss"] = list(loss)
        error = series.get(error_metric)
        if error:
            for step, v in enumerate(error):
                mlflow.log_metric(f"{prefix}_{name}_accuracy_curve", 1.0 - v, step=step)
            clave = "accuracy" if name == "train" else "val_accuracy"
            curvas[clave] = [1.0 - v for v in error]

    if curvas:
        _persistir_curvas(curvas, MODEL_DIRS[prefix])


def _persistir_curvas(curvas: dict[str, list[float]], clave: str) -> None:
    """Escribe training_history.csv + learning_curves.png bajo artifacts/."""
    from src.modeling.figures import plot_model_curves, write_history

    n = min(len(v) for v in curvas.values())
    filas = [{k: float(v[i]) for k, v in curvas.items()} for i in range(n)]
    out_dir = ARTIFACT_ROOT / clave
    write_history(out_dir / "training_history.csv", filas, "boosting_round")
    plot_model_curves(clave, filas, "boosting_round", out_dir)


def _balanced_sample_weight(y: pd.Series) -> np.ndarray:
    """Inverse-frequency per-class sample weights (class balancing)."""
    counts = y.value_counts()
    w = np.ones(len(y), dtype=float)
    for label, c in counts.items():
        w[y.values == label] = len(y) / (len(counts) * c)
    return w


def _log_operational(operational: dict, prefix: str) -> None:
    """Log operational metrics (model + greedy) to the active MLflow run."""
    for agg in ("model", "greedy"):
        for k, v in operational[agg].items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    mlflow.log_metric(f"{prefix}_{agg}_{k}_{sub_k}", sub_v)
            elif isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool):
                mlflow.log_metric(f"{prefix}_{agg}_{k}", v)


def _confusion_matrix_figure(
    y_true, y_pred, title: str, out_path: Path | None = None
) -> matplotlib.figure.Figure:
    """Matriz de confusión sobre índices canónicos, con el renderizador común.

    Se dibuja con `src.modeling.figures.plot_confusion_matrix`, el mismo que usan
    el MLP y los dos clásicos: antes había tres implementaciones distintas y sólo
    una normalizaba por fila, así que las figuras de los seis modelos no se
    podían poner una al lado de otra.
    """
    from src.modeling.figures import etiquetas_canonicas, plot_confusion_matrix

    k = int(max(y_true.max(), y_pred.max()))
    cm = confusion_matrix(y_true, y_pred, labels=list(range(k + 1)))
    return plot_confusion_matrix(cm.tolist(), etiquetas_canonicas(k + 1), title, out_path)


def _prediction_rows(results, split: str) -> pd.DataFrame:
    """Canonical target/predicted indices from EpisodeResult objects."""
    return pd.DataFrame(
        {
            "y_true": np.concatenate([r.target_index for r in results]),
            "y_pred": np.concatenate([r.predicted_index for r in results]),
            "split": split,
        }
    )


def report_confusion_matrices(
    xgb_predictions: pd.DataFrame,
    lgb_predictions: pd.DataFrame,
    att_predictions: pd.DataFrame,
    xgb_results: dict = None,
    lgb_results: dict = None,
) -> dict:
    """Render the pipeline's confusion matrices from cached predictions. Pure
    function: figures depend only on (y_true, y_pred), never on retraining.

    **These go to the Kedro catalog only.** The versioned figure under
    ``artifacts/<modelo>/confusion_matrix.png`` is written by
    ``scripts/report_figures.py``, from the ``confusion_matrix`` inside each
    model's results JSON -- the same numbers the comparison table publishes.

    One writer per file, and the reason is measured: for the transformer these
    two sources disagree on 200 of 66.399 rows. ``att_predictions`` comes from
    ``predict_with_capacity``, which decodes over the **float32** batch tensors,
    while the operational report decodes the same episodes in **float64**, so the
    capacity check flips on the margin (the ~1e-7 ``max_overflow_cu`` documented
    in docs/metricas.md). Neither is wrong, but if both wrote the same PNG the
    figure would contradict the table depending on which ran last.
    """
    figs = {}
    for split in ("train", "val"):
        for prefix, preds in (("xgb", xgb_predictions), ("lgb", lgb_predictions)):
            sub = preds[preds["split"] == split]
            figs[f"{prefix}_confusion_matrix_{split}"] = _confusion_matrix_figure(
                sub["y_true"],
                sub["y_pred"],
                f"{PRESENTACION[MODEL_DIRS[prefix]].etiqueta} — "
                f"{'validación' if split == 'val' else 'entrenamiento'}",
            )
    figs["att_confusion_matrix_val"] = _confusion_matrix_figure(
        att_predictions["y_true"],
        att_predictions["y_pred"],
        PRESENTACION[MODEL_DIRS["att"]].titulo_matriz,
    )

    for prefix, preds, results in (
        ("xgb", xgb_predictions, xgb_results or {}),
        ("lgb", lgb_predictions, lgb_results or {}),
    ):
        run_id = results.get("run_id")
        if not run_id:
            continue
        val = preds[preds["split"] == "val"]
        fig = _confusion_matrix_figure(
            val["y_true"], val["y_pred"], PRESENTACION[MODEL_DIRS[prefix]].titulo_matriz
        )
        with mlflow.start_run(run_id=run_id):
            mlflow.log_figure(fig, "confusion_matrix.png")

    return figs


def _save_model_artifact(name: str, classifier, scaler, classes, max_trucks) -> None:
    """Persist classifier + preprocessing schema for extrapolation evaluation."""
    out = ARTIFACT_ROOT / name
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "pairwise_schema.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "classes": classes,
                "max_trucks_padding": int(max_trucks),
                "blocks": scaler.to_dict(),
            },
            fh,
            indent=2,
            ensure_ascii=False,
        )
    import joblib

    joblib.dump(classifier, out / "classifier.joblib")


def encode_features(vehicles: pd.DataFrame, episodes: pd.DataFrame) -> pd.DataFrame:
    """Join vehicles + episodes, keep the teacher columns needed by the pairwise
    tensors (truck_capacities, n_loaded, cu_utilized) and drop non-optimal
    episodes. No truck-count-specific feature engineering: the models consume
    the canonical pairwise tensors from ``src.modeling``.
    """
    # `iso_year` es obligatorio: es el eje de la partición temporal compartida
    # (src/modeling/protocol.py). Antes se descartaba aquí, que es parte de por
    # qué este pipeline acabó particionando al azar.
    keep_ep = [
        "episode_id",
        "iso_year",
        "truck_capacities",
        "n_loaded",
        "cu_utilized",
        "optimal",
    ]
    df = vehicles.merge(episodes[keep_ep], on="episode_id", how="inner", validate="many_to_one")
    return df


def split_data(df: pd.DataFrame, split_params: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Particiona con el protocolo único del proyecto.

    Antes usaba `GroupShuffleSplit(test_size=0.2, random_state=42)`, mientras el
    MLP usaba holdout temporal, y ambas cifras se publicaban en la misma tabla.
    Ahora los cuatro modelos comparten `src.modeling.protocol.make_splits`, que
    además descarta los episodios no óptimos y comprueba que no haya fugas
    entre particiones.

    Devuelve (train, val) porque es lo que consume el pipeline Kedro; `test`
    queda reservado para el reporte final y no se toca durante el entrenamiento.
    """
    config = SplitConfig.from_mapping(split_params)
    bundle = make_splits(df, config)
    return bundle["train"], bundle["val"]


def _gbt_classifier_metrics(classifier, val_eps, val_arrays, scaler, classes, policy):
    """Capacity-aware val evaluation: logits -> decode -> episode-level metrics."""

    def predict_proba(x):
        return np.asarray(classifier.predict_proba(x))

    val_logits_by_ep = {
        i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(val_eps)
    }
    val_logits = stack_episode_logits(val_eps, val_arrays, val_logits_by_ep)

    results = evaluate_model(val_eps, val_arrays, val_logits, policy, len(classes))
    acc = accuracy_score(
        np.concatenate([r.target_index for r in results]),
        np.concatenate([r.predicted_index for r in results]),
    )
    f1 = _compute_defer_f1(
        np.concatenate([r.target_index for r in results]),
        np.concatenate([r.predicted_index for r in results]),
    )
    return results, acc, f1


def train_xgboost(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    episodes: pd.DataFrame,  # kept for pipeline compatibility; tensors carry teacher data
    max_depth: int,
    learning_rate: float,
    n_estimators: int,
    subsample: float,
    colsample_bytree: float,
    min_child_weight: int,
    scale_pos_weight: float,
    max_delta_step: int,
    seed: int,
    run_name: str,
) -> dict:
    import mlflow.xgboost
    import xgboost as xgb

    classes = derive_classes(train_df)
    train_eps, train_arrays, scaler = build_tensors(train_df, classes)
    val_eps, val_arrays, _ = build_tensors(val_df, classes, scaler, train_arrays.max_trucks)

    X, y = option_rows(train_eps, scaler)
    X_val, y_val = option_rows(val_eps, scaler)

    params = {
        "max_depth": max_depth,
        "learning_rate": learning_rate,
        "n_estimators": n_estimators,
        "subsample": subsample,
        "colsample_bytree": colsample_bytree,
        "min_child_weight": min_child_weight,
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "error"],
        "verbosity": 0,
        # `subsample` y `colsample_bytree` muestrean en cada ronda: sin semilla,
        # dos corridas con los mismos datos daban cifras distintas y la tabla
        # publicada no se podía reproducir.
        "random_state": seed,
    }
    sample_weight = _balanced_sample_weight(pd.Series(y))

    model = xgb.XGBClassifier(**params)
    with mlflow.start_run(run_name=run_name):
        mlflow.xgboost.autolog(log_models=False, silent=True)
        model.fit(
            X,
            y,
            eval_set=[(X, y), (X_val, y_val)],
            sample_weight=sample_weight,
            verbose=False,
        )
        run_id = mlflow.active_run().info.run_id

    with mlflow.start_run(run_id=run_id):
        mlflow.log_params({f"xgb_{k}": v for k, v in params.items()})
        mlflow.log_params(
            {
                "xgb_feature_space": "pairwise src/modeling tensors (vehicle ⊕ truck ⊕ context)",
                "xgb_canonical": "fleet by capacity desc; 0=SIN_CAMION, 1..T",
            }
        )
        _log_gbt_curves(model, "logloss", "error", "xgb")

        def predict_proba(x):
            return np.asarray(model.predict_proba(x))

        val_logits_by_ep = {
            i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(val_eps)
        }
        val_logits = stack_episode_logits(val_eps, val_arrays, val_logits_by_ep)
        policy = select_policy(val_eps, val_arrays, val_logits, len(classes))
        results, acc, f1 = _gbt_classifier_metrics(
            model, val_eps, val_arrays, scaler, classes, policy
        )
        model_metrics, greedy_metrics = evaluate_split(
            val_eps, val_arrays, val_logits, classes, policy
        )
        from fleet_loading.pipelines.training.pairwise import measure_latency

        latency = measure_latency(val_eps, val_arrays, val_logits, policy)
        operational = {
            "model": {**model_metrics, "latency": latency},
            "greedy": {**greedy_metrics, "latency": latency},
        }
        _log_operational(operational, "xgb")

        mlflow.log_metric("xgb_rawrow_accuracy", acc)
        mlflow.log_metric("xgb_rawrow_defer_f1", f1)
        mlflow.log_param("xgb_decoder_policy", policy)
        mlflow.sklearn.log_model(model, "model", serialization_format="pickle")
        _save_model_artifact("xgboost", model, scaler, classes, train_arrays.max_trucks)

        train_logits = stack_episode_logits(
            train_eps,
            train_arrays,
            {i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(train_eps)},
        )
        train_results = evaluate_model(train_eps, train_arrays, train_logits, policy, len(classes))
        predictions = pd.concat(
            [
                _prediction_rows(train_results, "train"),
                _prediction_rows(results, "val"),
            ],
            ignore_index=True,
        )

        return {
            "xgb_results": {
                # Diagnóstico del clasificador crudo, no cifra publicable: la
                # tabla lee `xgb_operational.model`, igual que las otras cinco filas.
                "xgb_rawrow_accuracy": acc,
                "xgb_rawrow_defer_f1": f1,
                "xgb_operational": operational,
                "xgb_decoder_policy": policy,
                # La tabla comparativa rechaza publicar una fila que no declare
                # su partición. Estas tres fuentes estaban exentas por no traer
                # la clave, que es medio agujero en la puerta que la vigila.
                "split_strategy": "time",
                "seed": seed,
                "run_id": run_id,
            },
            "xgb_predictions": predictions,
        }


def train_lightgbm(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    episodes: pd.DataFrame,  # kept for pipeline compatibility; tensors carry teacher data
    num_leaves: int,
    learning_rate: float,
    n_estimators: int,
    subsample: float,
    colsample_bytree: float,
    min_child_samples: int,
    scale_pos_weight: float,
    seed: int,
    run_name: str,
) -> dict:
    import lightgbm as lgb
    import mlflow.lightgbm

    classes = derive_classes(train_df)
    train_eps, train_arrays, scaler = build_tensors(train_df, classes)
    val_eps, val_arrays, _ = build_tensors(val_df, classes, scaler, train_arrays.max_trucks)

    X, y = option_rows(train_eps, scaler)
    X_val, y_val = option_rows(val_eps, scaler)

    params = {
        "num_leaves": num_leaves,
        "learning_rate": learning_rate,
        "n_estimators": n_estimators,
        "subsample": subsample,
        "colsample_bytree": colsample_bytree,
        "min_child_samples": min_child_samples,
        "objective": "binary",
        "verbosity": -1,
        "random_state": seed,  # mismo motivo que en XGBoost
    }
    sample_weight = _balanced_sample_weight(pd.Series(y))

    model = lgb.LGBMClassifier(**params)
    with mlflow.start_run(run_name=run_name):
        mlflow.lightgbm.autolog(log_models=False, silent=True)
        model.fit(
            X,
            y,
            eval_set=[(X, y), (X_val, y_val)],
            eval_metric=["binary_logloss", "binary_error"],
            sample_weight=sample_weight,
            callbacks=[lgb.early_stopping(50)],
        )
        run_id = mlflow.active_run().info.run_id

    with mlflow.start_run(run_id=run_id):
        mlflow.log_params({f"lgb_{k}": v for k, v in params.items()})
        mlflow.log_params(
            {
                "lgb_feature_space": "pairwise src/modeling tensors (vehicle ⊕ truck ⊕ context)",
                "lgb_canonical": "fleet by capacity desc; 0=SIN_CAMION, 1..T",
            }
        )
        _log_gbt_curves(model, "binary_logloss", "binary_error", "lgb")

        def predict_proba(x):
            return np.asarray(model.predict_proba(x))

        val_logits_by_ep = {
            i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(val_eps)
        }
        val_logits = stack_episode_logits(val_eps, val_arrays, val_logits_by_ep)
        policy = select_policy(val_eps, val_arrays, val_logits, len(classes))
        results, acc, f1 = _gbt_classifier_metrics(
            model, val_eps, val_arrays, scaler, classes, policy
        )
        model_metrics, greedy_metrics = evaluate_split(
            val_eps, val_arrays, val_logits, classes, policy
        )
        from fleet_loading.pipelines.training.pairwise import measure_latency

        latency = measure_latency(val_eps, val_arrays, val_logits, policy)
        operational = {
            "model": {**model_metrics, "latency": latency},
            "greedy": {**greedy_metrics, "latency": latency},
        }
        _log_operational(operational, "lgb")

        mlflow.log_metric("lgb_rawrow_accuracy", acc)
        mlflow.log_metric("lgb_rawrow_defer_f1", f1)
        mlflow.log_param("lgb_decoder_policy", policy)
        mlflow.sklearn.log_model(model, "model", serialization_format="pickle")
        _save_model_artifact("lightgbm", model, scaler, classes, train_arrays.max_trucks)

        train_logits = stack_episode_logits(
            train_eps,
            train_arrays,
            {i: logits_from_proba(ep, scaler, predict_proba) for i, ep in enumerate(train_eps)},
        )
        train_results = evaluate_model(train_eps, train_arrays, train_logits, policy, len(classes))
        predictions = pd.concat(
            [
                _prediction_rows(train_results, "train"),
                _prediction_rows(results, "val"),
            ],
            ignore_index=True,
        )

        return {
            "lgb_results": {
                # Diagnóstico del clasificador crudo, no cifra publicable: la
                # tabla lee `lgb_operational.model`, igual que las otras cinco filas.
                "lgb_rawrow_accuracy": acc,
                "lgb_rawrow_defer_f1": f1,
                "lgb_operational": operational,
                "lgb_decoder_policy": policy,
                # La tabla comparativa rechaza publicar una fila que no declare
                # su partición. Estas tres fuentes estaban exentas por no traer
                # la clave, que es medio agujero en la puerta que la vigila.
                "split_strategy": "time",
                "seed": seed,
                "run_id": run_id,
            },
            "lgb_predictions": predictions,
        }


def train_attention(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    episodes: pd.DataFrame,
    d_model: int,
    nhead: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    learning_rate: float,
    n_epochs: int,
    seed: int,
    run_name: str,
) -> dict:
    from fleet_loading.pipelines.training.attention_model import train_attention as _train

    return _train(
        train_df,
        val_df,
        episodes,
        d_model,
        nhead,
        num_layers,
        dropout,
        batch_size,
        learning_rate,
        n_epochs,
        seed,
        run_name,
    )
