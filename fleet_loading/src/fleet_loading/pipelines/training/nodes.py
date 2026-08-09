from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow

MLFLOW_DB = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "mlflow.db")
mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB}")

REPO_ROOT = Path(__file__).resolve().parents[5]
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "fleet_loading"

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit

from src.modeling.metrics import evaluate_model

from fleet_loading.pipelines.training.pairwise import (
    build_tensors,
    derive_classes,
    evaluate_split,
    logits_from_proba,
    option_rows,
    select_policy,
    stack_episode_logits,
)

# Canonical index space (shared with src/modeling): 0 = SIN_CAMION, 1..T = truck
# by capacity descending. No hardcoded truck count: the models are pairwise and
# accept any T.
DEFER_LABEL = 0


def _compute_defer_f1(y_true, y_pred) -> float:
    """F1 for the defer class (canonical index 0) vs everything else."""
    return f1_score(
        (y_true == DEFER_LABEL).astype(int),
        (y_pred == DEFER_LABEL).astype(int),
        zero_division=0,
    )


def _log_gbt_curves(model, metric_name: str, error_metric: str, prefix: str) -> None:
    """Re-log a GBT's train/val loss and accuracy curves under clear MLflow names.

    Both XGBoost and LightGBM record per-round eval results in ``evals_result``
    keyed as ``validation_0``/``validation_1`` (XGB) or ``training``/``valid_1``
    (LGB). ``mlflow.autolog`` logs these under those framework names; we re-log
    them as ``<prefix>_train_<metric>`` / ``<prefix>_val_<metric>`` so the MLflow
    UI is unambiguous. Accuracy is logged as ``1 - error`` from the framework's
    error metric.
    """
    result = getattr(model, "evals_result", None)
    result = result() if callable(result) else getattr(model, "_evals_result", None)
    if not result:
        return
    train_series = result.get("validation_0") or result.get("training")
    val_series = (
        result.get("validation_1")
        or result.get("valid_1")
        or result.get("valid_0")
    )
    for name, series in (("train", train_series), ("val", val_series)):
        if not series:
            continue
        loss = series.get(metric_name) or next(iter(series.values()))
        for step, v in enumerate(loss):
            mlflow.log_metric(f"{prefix}_{name}_{metric_name}", v, step=step)
        error = series.get(error_metric)
        if error:
            for step, v in enumerate(error):
                mlflow.log_metric(f"{prefix}_{name}_accuracy_curve", 1.0 - v, step=step)


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
    y_true, y_pred, title: str, normalized: bool = False
) -> "matplotlib.figure.Figure":
    """Render a per-truck confusion matrix over canonical indices.

    Labels are dynamic: ``Sin camión`` + one column per truck index actually
    present, where index ``i`` is the ``i``-th largest truck of its episode
    (canonicalization). Never depends on a fixed truck count.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay

    k = int(max(y_true.max(), y_pred.max()))
    labels = [f"Cam{i + 1}" for i in range(k)] + ["Sin camión"]
    cm = confusion_matrix(
        y_true, y_pred, labels=list(range(k + 1)),
        normalize="true" if normalized else None,
    )
    disp = ConfusionMatrixDisplay(cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(title)
    ax.set_xlabel("Predicción (truck asignado)")
    ax.set_ylabel("Real (truck asignado)")
    ax.tick_params(axis="x", rotation=45)
    return fig


def _prediction_rows(results, split: str) -> pd.DataFrame:
    """Canonical target/predicted indices from EpisodeResult objects."""
    return pd.DataFrame({
        "y_true": np.concatenate([r.target_index for r in results]),
        "y_pred": np.concatenate([r.predicted_index for r in results]),
        "split": split,
    })


def report_confusion_matrices(
    xgb_predictions: pd.DataFrame,
    lgb_predictions: pd.DataFrame,
    att_predictions: pd.DataFrame,
    xgb_results: dict = None,
    lgb_results: dict = None,
) -> dict:
    """Render all confusion matrices from cached predictions. Pure function:
    figures depend only on (y_true, y_pred), never on retraining. Also
    overwrites the model runs' ``confusion_matrix.png`` with a readable version."""
    figs = {}
    for split in ("train", "val"):
        for prefix, preds in (("xgb", xgb_predictions), ("lgb", lgb_predictions)):
            sub = preds[preds["split"] == split]
            figs[f"{prefix}_confusion_matrix_{split}"] = _confusion_matrix_figure(
                sub["y_true"], sub["y_pred"],
                f"{prefix} confusion matrix ({split})",
            )
    figs["att_confusion_matrix_val"] = _confusion_matrix_figure(
        att_predictions["y_true"], att_predictions["y_pred"],
        "attention capacity-aware confusion matrix (val)",
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
            val["y_true"], val["y_pred"],
            "Normalized confusion matrix",
            normalized=True,
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


def encode_features(
    vehicles: pd.DataFrame, episodes: pd.DataFrame
) -> pd.DataFrame:
    """Join vehicles + episodes, keep the teacher columns needed by the pairwise
    tensors (truck_capacities, n_loaded, cu_utilized) and drop non-optimal
    episodes. No truck-count-specific feature engineering: the models consume
    the canonical pairwise tensors from ``src.modeling``.
    """
    keep_ep = ["episode_id", "truck_capacities", "n_loaded", "cu_utilized", "optimal"]
    df = vehicles.merge(
        episodes[keep_ep], on="episode_id", how="inner", validate="many_to_one"
    )
    df = df[df["optimal"].astype(bool)].reset_index(drop=True)
    return df.drop(columns=["optimal"])


def split_data(
    df: pd.DataFrame, test_size: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    episodes = df[["episode_id"]].drop_duplicates()
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=42
    )
    train_idx, val_idx = next(
        splitter.split(episodes, groups=episodes["episode_id"])
    )

    train_ep = episodes.iloc[train_idx]["episode_id"]
    val_ep = episodes.iloc[val_idx]["episode_id"]

    train_df = df[df["episode_id"].isin(train_ep)].reset_index(drop=True)
    val_df = df[df["episode_id"].isin(val_ep)].reset_index(drop=True)

    return train_df, val_df


def _gbt_classifier_metrics(classifier, val_eps, val_arrays, scaler, classes, policy):
    """Capacity-aware val evaluation: logits -> decode -> episode-level metrics."""
    predict_proba = lambda x: np.asarray(classifier.predict_proba(x))
    val_logits_by_ep = {
        i: logits_from_proba(ep, scaler, predict_proba)
        for i, ep in enumerate(val_eps)
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
    run_name: str,
) -> dict:
    import xgboost as xgb
    import mlflow.xgboost

    classes = derive_classes(train_df)
    train_eps, train_arrays, scaler = build_tensors(train_df, classes)
    val_eps, val_arrays, _ = build_tensors(
        val_df, classes, scaler, train_arrays.max_trucks
    )

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
    }
    sample_weight = _balanced_sample_weight(pd.Series(y))

    model = xgb.XGBClassifier(**params)
    with mlflow.start_run(run_name=run_name):
        mlflow.xgboost.autolog(log_models=False, silent=True)
        model.fit(
            X, y,
            eval_set=[(X, y), (X_val, y_val)],
            sample_weight=sample_weight,
            verbose=False,
        )
        run_id = mlflow.active_run().info.run_id

    with mlflow.start_run(run_id=run_id):
        mlflow.log_params({f"xgb_{k}": v for k, v in params.items()})
        mlflow.log_params({
            "xgb_feature_space": "pairwise src/modeling tensors (vehicle ⊕ truck ⊕ context)",
            "xgb_canonical": "fleet by capacity desc; 0=SIN_CAMION, 1..T",
        })
        _log_gbt_curves(model, "logloss", "error", "xgb")

        predict_proba = lambda x: np.asarray(model.predict_proba(x))
        val_logits_by_ep = {
            i: logits_from_proba(ep, scaler, predict_proba)
            for i, ep in enumerate(val_eps)
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
        operational = {"model": {**model_metrics, "latency": latency},
                       "greedy": {**greedy_metrics, "latency": latency}}
        _log_operational(operational, "xgb")

        mlflow.log_metric("xgb_val_accuracy", acc)
        mlflow.log_metric("xgb_val_defer_f1", f1)
        mlflow.log_param("xgb_decoder_policy", policy)
        mlflow.sklearn.log_model(
            model, "model", serialization_format="pickle"
        )
        _save_model_artifact("xgboost", model, scaler, classes, train_arrays.max_trucks)

        train_logits = stack_episode_logits(train_eps, train_arrays, {
            i: logits_from_proba(ep, scaler, predict_proba)
            for i, ep in enumerate(train_eps)
        })
        train_results = evaluate_model(
            train_eps, train_arrays, train_logits, policy, len(classes)
        )
        predictions = pd.concat([
            _prediction_rows(train_results, "train"),
            _prediction_rows(results, "val"),
        ], ignore_index=True)

        return {
            "xgb_results": {
                "xgb_val_accuracy": acc,
                "xgb_val_defer_f1": f1,
                "xgb_operational": operational,
                "xgb_decoder_policy": policy,
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
    run_name: str,
) -> dict:
    import lightgbm as lgb
    import mlflow.lightgbm

    classes = derive_classes(train_df)
    train_eps, train_arrays, scaler = build_tensors(train_df, classes)
    val_eps, val_arrays, _ = build_tensors(
        val_df, classes, scaler, train_arrays.max_trucks
    )

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
    }
    sample_weight = _balanced_sample_weight(pd.Series(y))

    model = lgb.LGBMClassifier(**params)
    with mlflow.start_run(run_name=run_name):
        mlflow.lightgbm.autolog(log_models=False, silent=True)
        model.fit(
            X, y,
            eval_set=[(X, y), (X_val, y_val)],
            eval_metric=["binary_logloss", "binary_error"],
            sample_weight=sample_weight,
            callbacks=[lgb.early_stopping(50)],
        )
        run_id = mlflow.active_run().info.run_id

    with mlflow.start_run(run_id=run_id):
        mlflow.log_params({f"lgb_{k}": v for k, v in params.items()})
        mlflow.log_params({
            "lgb_feature_space": "pairwise src/modeling tensors (vehicle ⊕ truck ⊕ context)",
            "lgb_canonical": "fleet by capacity desc; 0=SIN_CAMION, 1..T",
        })
        _log_gbt_curves(model, "binary_logloss", "binary_error", "lgb")

        predict_proba = lambda x: np.asarray(model.predict_proba(x))
        val_logits_by_ep = {
            i: logits_from_proba(ep, scaler, predict_proba)
            for i, ep in enumerate(val_eps)
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
        operational = {"model": {**model_metrics, "latency": latency},
                       "greedy": {**greedy_metrics, "latency": latency}}
        _log_operational(operational, "lgb")

        mlflow.log_metric("lgb_val_accuracy", acc)
        mlflow.log_metric("lgb_val_defer_f1", f1)
        mlflow.log_param("lgb_decoder_policy", policy)
        mlflow.sklearn.log_model(
            model, "model", serialization_format="pickle"
        )
        _save_model_artifact("lightgbm", model, scaler, classes, train_arrays.max_trucks)

        train_logits = stack_episode_logits(train_eps, train_arrays, {
            i: logits_from_proba(ep, scaler, predict_proba)
            for i, ep in enumerate(train_eps)
        })
        train_results = evaluate_model(
            train_eps, train_arrays, train_logits, policy, len(classes)
        )
        predictions = pd.concat([
            _prediction_rows(train_results, "train"),
            _prediction_rows(results, "val"),
        ], ignore_index=True)

        return {
            "lgb_results": {
                "lgb_val_accuracy": acc,
                "lgb_val_defer_f1": f1,
                "lgb_operational": operational,
                "lgb_decoder_policy": policy,
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
    run_name: str,
) -> dict:
    from fleet_loading.pipelines.training.attention_model import train_attention as _train

    return _train(
        train_df, val_df, episodes,
        d_model, nhead, num_layers, dropout,
        batch_size, learning_rate, n_epochs, run_name,
    )
