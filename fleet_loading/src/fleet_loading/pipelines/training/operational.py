"""Operational metrics for the fleet-loading models.

Computes, per episode, the delivery's three formal metrics against the exact
teacher (``episodes.parquet`` already carries ``n_loaded`` / ``cu_utilized``
per episode, i.e. ``V_exact`` for every manifest):

1. **Eficiencia de llenado volumétrico** -- CU used / total capacity.
2. **Tiempo de cómputo** -- milliseconds from manifest to full assignment.
3. **Brecha óptima** -- ``(V_teacher - V_model) / V_teacher``, i.e. how much
   worse than the exact optimum the model is on the primary objective
   (vehicles loaded). On small instances the teacher IS the brute-force
   optimum, so this is the delivery's "brecha en instancias acotadas".

All plans produced here are **feasible by construction**: the decoder only
places a vehicle when it fits, so no truck is ever over capacity. That is the
hard invariant of the pipeline, matching ``capacity_decoder.py``.

The greedy baseline (largest vehicle first) is the manual heuristic the report
describes and the delivery asks to beat.
"""

from __future__ import annotations

import time

import numpy as np

DEFERRED = -1
_TOL = 1e-9
# Overflow below this is float32 measurement noise (CU values up to ~6.0 only
# carry ~7 decimal digits in float32, so residuals reach ~1e-7). All decoders
# are feasible by construction; this keeps the violation flag honest.
_VIOLATION_TOL = 1e-6

# Human-readable axis labels for the per-truck confusion matrices.
CONFUSION_LABELS = ["Camión 1", "Camión 2", "Camión 3", "Camión 4", "Sin camión"]


def greedy_first_fit(cu: np.ndarray, capacities: np.ndarray) -> np.ndarray:
    """Largest-first pack (the report's manual heuristic). Returns assignment."""
    caps = np.asarray(capacities, dtype=float)
    cus = np.asarray(cu, dtype=float)
    assign = np.full(len(cus), DEFERRED, dtype=int)
    remaining = caps.copy()

    for i in np.argsort(-cus, kind="stable"):
        for j in range(len(caps)):
            if cus[i] <= remaining[j] + _TOL:
                assign[i] = j
                remaining[j] -= cus[i]
                break
    return assign


def plan_from_scores(cu: np.ndarray, capacities: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """Model ranks vehicles by score desc; pack those that fit, first-fit.

    Under the teacher's lexicographic objective (max count, then max CU),
    loading more is always better, so the decoder loads every vehicle it can
    and only defers when capacity is exhausted -- vehicles ranked lowest by the
    model are the ones that lose out. That makes the model's *priority* the
    learnable signal and keeps the plan feasible.
    """
    caps = np.asarray(capacities, dtype=float)
    cus = np.asarray(cu, dtype=float)
    scores = np.asarray(scores, dtype=float)
    assign = np.full(len(cus), DEFERRED, dtype=int)
    remaining = caps.copy()

    for i in np.argsort(-scores, kind="stable"):
        for j in range(len(caps)):
            if cus[i] <= remaining[j] + _TOL:
                assign[i] = j
                remaining[j] -= cus[i]
                break
    return assign


def plan_from_truck_probs(
    cu: np.ndarray,
    capacities: np.ndarray,
    probs: np.ndarray,  # (V, n_trucks+1): truck probs then defer
) -> np.ndarray:
    """Capacity-aware per-truck decode from multiclass probs.

    Mirrors ``capacity_decoder.decode_episode`` (policy "model"): vehicles are
    ranked by loading margin (best truck prob minus defer prob), and each is
    placed on the model's most preferred truck that still fits. The plan is
    feasible by construction.
    """
    caps = np.asarray(capacities, dtype=float)
    cus = np.asarray(cu, dtype=float)
    probs = np.asarray(probs, dtype=float)
    n_trucks = len(caps)
    assign = np.full(len(cus), DEFERRED, dtype=int)
    remaining = caps.copy()

    if n_trucks == 0 or len(cus) == 0:
        return assign

    truck_probs = probs[:, :n_trucks]
    defer_probs = probs[:, n_trucks]
    margin = truck_probs.max(axis=1) - defer_probs

    for i in np.argsort(-margin, kind="stable"):
        order = np.argsort(-truck_probs[i], kind="stable")
        for j in order:
            if cus[i] <= remaining[j] + _TOL:
                assign[i] = j
                remaining[j] -= cus[i]
                break
    return assign


def _plan_stats(assign: np.ndarray, cu: np.ndarray, capacities: np.ndarray) -> tuple[int, float, float]:
    caps = np.asarray(capacities, dtype=float)
    cus = np.asarray(cu, dtype=float)
    loads = np.zeros_like(caps)
    n_loaded = 0
    for i, j in enumerate(assign):
        if j != DEFERRED:
            loads[j] += cus[i]
            n_loaded += 1
    return n_loaded, float(loads.sum()), float(np.max(loads - caps, initial=0.0))
def episode_report(
    ep_id: str,
    assign: np.ndarray,
    cu: np.ndarray,
    capacities: np.ndarray,
    teacher_n_loaded: int,
    teacher_cu: float,
) -> dict:
    n_loaded, model_cu, overflow = _plan_stats(assign, cu, capacities)
    return {
        "episode_id": ep_id,
        "n_vehicles": int(len(cu)),
        "n_trucks": int(len(capacities)),
        "total_capacity": float(np.asarray(capacities, dtype=float).sum()),
        "model_n_loaded": n_loaded,
        "teacher_n_loaded": int(teacher_n_loaded),
        "model_cu": model_cu,
        "teacher_cu": float(teacher_cu),
        "max_overflow": overflow,
    }


def aggregate_operational(rows: list[dict], latency_ms: list[float]) -> dict:
    """Aggregate per-episode reports into the report-ready summary."""
    if not rows:
        raise ValueError("No hay episodios sobre los que agregar métricas operativas.")

    model_loaded = np.array([r["model_n_loaded"] for r in rows], dtype=float)
    teacher_loaded = np.array([r["teacher_n_loaded"] for r in rows], dtype=float)
    model_cu = np.array([r["model_cu"] for r in rows], dtype=float)
    teacher_cu = np.array([r["teacher_cu"] for r in rows], dtype=float)
    capacity = np.array([r["total_capacity"] for r in rows], dtype=float)
    overflow = np.array([r["max_overflow"] for r in rows], dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        rel_gap = np.where(teacher_loaded > 0, (teacher_loaded - model_loaded) / teacher_loaded, 0.0)

    n = len(rows)
    return {
        # 1. Feasibility: must be 0, or nothing else matters.
        "capacity_violation_rate": float((overflow > _VIOLATION_TOL).mean()),
        "max_overflow_cu": float(overflow.max()),
        # 2. Primary objective: vehicles loaded vs exact teacher.
        "loaded_gap_mean": float((teacher_loaded - model_loaded).mean()),
        "episodes_matching_teacher_count_pct": float(100.0 * (model_loaded == teacher_loaded).mean()),
        "optimality_gap_loaded_pct": float(100.0 * rel_gap.mean()),
        # 3. Secondary objective: CU utilization (delivery's fill efficiency).
        "cu_gap_mean": float((teacher_cu - model_cu).mean()),
        "cu_utilization_model_pct": float(100.0 * model_cu.sum() / capacity.sum()),
        "cu_utilization_teacher_pct": float(100.0 * teacher_cu.sum() / capacity.sum()),
        # Deferred totals.
        "deferred_model_total": int((n * 0) + (teacher_loaded.sum() - model_loaded.sum())),
        "deferred_teacher_total": int((capacity.sum() * 0) + sum(
            int(np.maximum(0, r["n_vehicles"] - r["teacher_n_loaded"])) for r in rows
        )),
        # Context + latency (delivery's compute-time metric).
        "n_episodes": n,
        "n_vehicle_rows": int(sum(r["n_vehicles"] for r in rows)),
        "latency": _latency_summary(latency_ms),
    }


def _latency_summary(ms: list[float]) -> dict:
    if not ms:
        return {"n_timed": 0, "mean_ms": 0.0, "median_ms": 0.0, "p99_ms": 0.0}
    t = np.asarray(ms, dtype=float)
    return {
        "n_timed": int(len(t)),
        "mean_ms": float(t.mean()),
        "median_ms": float(np.median(t)),
        "p99_ms": float(np.quantile(t, 0.99)),
    }


def gbt_plans(
    predict_proba,  # callable(row_df) -> (n,) P(loaded)
    val_df,
    episodes,
    feature_cols: list[str],
    sample_limit: int | None = None,
):
    """Build a feasible plan per episode from a binary P(loaded) classifier.

    Returns ``(rows, latency_ms)`` where ``rows`` are per-episode reports.
    """
    rows: list[dict] = []
    latency: list[float] = []
    ep = episodes.set_index("episode_id")

    groups = list(val_df.groupby("episode_id", sort=False))
    if sample_limit:
        rng = np.random.default_rng(0)
        groups = rng.choice(groups, size=min(sample_limit, len(groups)), replace=False)

    for ep_id, g in groups:
        caps = np.asarray(ep.loc[ep_id, "truck_capacities"], dtype=float)
        cu = g["cu"].values.astype(float)
        teacher_n = int(ep.loc[ep_id, "n_loaded"])
        teacher_cu = float(ep.loc[ep_id, "cu_utilized"])

        t0 = time.perf_counter()
        p = predict_proba(g[feature_cols])  # P(loaded)
        assign = plan_from_scores(cu, caps, p)
        latency.append((time.perf_counter() - t0) * 1000.0)

        rows.append(episode_report(ep_id, assign, cu, caps, teacher_n, teacher_cu))

    return rows, latency


def gbt_truck_plans(
    predict_proba,  # callable(row_df) -> (n, n_trucks+1) multiclass probs
    val_df,
    episodes,
    feature_cols: list[str],
    sample_limit: int | None = None,
):
    """Build a feasible per-truck plan per episode from a multiclass classifier.

    Returns ``(rows, latency_ms)`` where ``rows`` are per-episode reports.
    """
    rows: list[dict] = []
    latency: list[float] = []
    ep = episodes.set_index("episode_id")

    groups = list(val_df.groupby("episode_id", sort=False))
    if sample_limit:
        rng = np.random.default_rng(0)
        groups = rng.choice(groups, size=min(sample_limit, len(groups)), replace=False)

    for ep_id, g in groups:
        caps = np.asarray(ep.loc[ep_id, "truck_capacities"], dtype=float)
        cu = g["cu"].values.astype(float)
        teacher_n = int(ep.loc[ep_id, "n_loaded"])
        teacher_cu = float(ep.loc[ep_id, "cu_utilized"])

        t0 = time.perf_counter()
        probs = predict_proba(g[feature_cols])  # (V, n_trucks+1)
        assign = plan_from_truck_probs(cu, caps, probs)
        latency.append((time.perf_counter() - t0) * 1000.0)

        rows.append(episode_report(ep_id, assign, cu, caps, teacher_n, teacher_cu))

    return rows, latency


def greedy_report(
    val_df,
    episodes,
    sample_limit: int | None = None,
):
    """Per-episode reports for the greedy (largest-first) baseline."""
    rows: list[dict] = []
    latency: list[float] = []
    ep = episodes.set_index("episode_id")

    groups = list(val_df.groupby("episode_id", sort=False))
    if sample_limit:
        rng = np.random.default_rng(0)
        groups = rng.choice(groups, size=min(sample_limit, len(groups)), replace=False)

    for ep_id, g in groups:
        caps = np.asarray(ep.loc[ep_id, "truck_capacities"], dtype=float)
        cu = g["cu"].values.astype(float)
        teacher_n = int(ep.loc[ep_id, "n_loaded"])
        teacher_cu = float(ep.loc[ep_id, "cu_utilized"])

        t0 = time.perf_counter()
        assign = greedy_first_fit(cu, caps)
        latency.append((time.perf_counter() - t0) * 1000.0)

        rows.append(episode_report(ep_id, assign, cu, caps, teacher_n, teacher_cu))

    return rows, latency
