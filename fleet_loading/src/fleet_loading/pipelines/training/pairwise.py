"""Shared pairwise machinery for the fleet_loading models.

The professor's requirement -- the models must work with **any number of
trucks** -- is a structural property: no model can have a slot ``CAMION_4``
baked in, because there is no ``CAMION_5``. The proven solution already exists
in ``src/modeling`` (the pairwise MLP): canonicalize the fleet by capacity,
express every vehicle as a set of ``(vehicle, truck)`` options plus a defer
option, score the options, and decode with a capacity-respecting greedy
decoder whose truck axis is ``None``.

This module feeds that exact machinery to the GBTs and the attention model:

* ``build_tensors`` -- canonicalization + vehicle/truck/context blocks
  (``src.modeling.features``), fit the ``BlockScaler`` on train only.
* ``option_rows`` / ``logits_from_proba`` -- the GBT view: one row per
  ``(vehicle, option)``, a single binary ``is_chosen`` classifier, and per
  episode ``(V, 1 + T)`` logits with ``SIN_CAMION`` at index 0.
* ``decode_and_report`` -- ``capacity_decoder.decode_episode`` + the
  episode-level aggregates from ``src.modeling.metrics`` for model, greedy
  baseline, and latency.

Both the GBTs and the attention model emit the same ``(V, 1 + T)`` logits in
the same canonical index space, so decoding, reporting, and extrapolation
(``scripts/build_extrapolation_set.py``, 5-10 trucks) are identical for all
three models.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.modeling.capacity_decoder import POLICIES, decode_episode  # noqa: E402
from src.modeling.features import (  # noqa: E402
    BlockScaler,
    build_all_episodes,
    build_model_arrays,
)
from src.modeling.metrics import (  # noqa: E402
    aggregate,
    episode_logits,
    evaluate_greedy,
    evaluate_model,
)

VEHICLE_DIM = 6
TRUCK_BLOCK_SIZE = 3

# Column layout of a GBT option row: pair space (vehicle ⊕ truck ⊕ context,
# 19 dims) plus an explicit ``is_defer`` flag, so the tree can learn the defer
# decision as a distinct head the same way the MLP's separate defer head does.
OPTION_ROW_SIZE = 19 + 1


def derive_classes(df: pd.DataFrame) -> list[str]:
    """Clases del dataset en orden canónico, compartido por las tres modelos."""
    return sorted(df["clase"].unique().tolist())


def build_tensors(
    df: pd.DataFrame,
    classes: list[str],
    scaler: BlockScaler | None = None,
    max_trucks: int | None = None,
) -> tuple[list, object, BlockScaler]:
    """EpisodeTensors + ModelArrays for a split, reusing ``src.modeling``.

    The scaler is fit by the caller on train and passed down, so train and val
    use identical standardization. ``max_trucks`` is only padding -- the truck
    axis stays ``None`` in every consumer, so any ``T`` works at inference.
    """
    episodes = build_all_episodes(df, classes)
    if scaler is None:
        scaler = BlockScaler.fit(episodes, classes)
    max_t = max_trucks or max(e.n_trucks for e in episodes)
    arrays = build_model_arrays(episodes, scaler, max_t)
    return episodes, arrays, scaler


# --------------------------------------------------------------------------- GBT
def option_rows_from_episode(episode, scaler: BlockScaler) -> tuple[np.ndarray, np.ndarray]:
    """``(V * (T + 1), 20)`` binary rows for one episode.

    Each vehicle contributes one row per real truck (pair features, ``is_defer=0``)
    and one defer row (vehicle ⊕ context, zeroed truck block, ``is_defer=1``).
    Label = 1 iff that option is the teacher's choice (``episode.target``).
    """
    v = scaler.transform("vehicle", episode.vehicle)
    t = scaler.transform("truck", episode.truck)
    g = scaler.transform("context", episode.context[None, :])[0]

    rows, y = [], []
    for i in range(episode.n_vehicles):
        for j in range(episode.n_trucks):
            rows.append(np.concatenate([v[i], t[j], g, [0.0]]))
            y.append(1 if episode.target[i] == j + 1 else 0)
        rows.append(np.concatenate([v[i], np.zeros(TRUCK_BLOCK_SIZE), g, [1.0]]))
        y.append(1 if episode.target[i] == 0 else 0)
    return np.asarray(rows, dtype=np.float32), np.asarray(y, dtype=np.int8)


def option_rows(episodes: list, scaler: BlockScaler) -> tuple[np.ndarray, np.ndarray]:
    """Concatenated option rows over all episodes (for GBT training)."""
    xs, ys = [], []
    for ep in episodes:
        x, y = option_rows_from_episode(ep, scaler)
        xs.append(x)
        ys.append(y)
    return np.concatenate(xs), np.concatenate(ys)


def logits_from_proba(episode, scaler: BlockScaler, predict_proba) -> np.ndarray:
    """Per-vehicle ``(V, 1 + T)`` logits from a binary ``is_chosen`` classifier.

    Option rows are ordered truck_0..truck_{T-1}, defer, so the defer column is
    the last of each vehicle's block. We reorder to the canonical index space:
    column 0 = SIN_CAMION, columns 1..T = trucks in canonical order.
    """
    x, _ = option_rows_from_episode(episode, scaler)
    p = np.asarray(predict_proba(x), dtype=np.float64)[:, 1]  # P(chosen)
    p = p.reshape(episode.n_vehicles, episode.n_trucks + 1)
    logits = np.zeros((episode.n_vehicles, episode.n_trucks + 1))
    logits[:, 0] = p[:, -1]
    logits[:, 1:] = p[:, :-1]
    return logits


# ------------------------------------------------------------------ evaluation
def stack_episode_logits(episodes: list, arrays, logits_by_episode: dict) -> np.ndarray:
    """Stack per-episode logits into a ``(N, max_trucks + 1)`` array for metrics."""
    max_t = arrays.max_trucks
    out = np.zeros((arrays.pair.shape[0], max_t + 1), dtype=np.float64)
    for ep_i, _ep in enumerate(episodes):
        rows = np.flatnonzero(arrays.episode_index == ep_i)
        lg = logits_by_episode[ep_i]
        out[rows, : lg.shape[1]] = lg
    return out


def measure_latency(episodes: list, arrays, logits: np.ndarray, policy: str) -> dict:
    """Decode latency per manifest: score assembly is model-specific, so we only
    time ``decode_episode`` (the shared, load-bearing step)."""
    timings = []
    for ep_i, ep in enumerate(episodes):
        rows = np.flatnonzero(arrays.episode_index == ep_i)
        t0 = time.perf_counter()
        decode_episode(
            episode_logits(logits, rows, ep.n_trucks),
            cu=ep.cu,
            capacities=ep.capacities,
            policy=policy,
        )
        timings.append((time.perf_counter() - t0) * 1000.0)
    t = np.asarray(timings)
    return {
        "n_manifests_timed": int(len(t)),
        "mean_ms": float(t.mean()),
        "median_ms": float(np.median(t)),
        "p99_ms": float(np.quantile(t, 0.99)),
    }


def evaluate_split(
    episodes: list,
    arrays,
    logits: np.ndarray,
    classes: list[str],
    policy: str = "count",
) -> tuple[dict, dict]:
    """``(model_metrics, greedy_metrics)`` via ``src.modeling.metrics``.

    Model plans come from ``decode_episode`` (feasible by construction); the
    greedy baseline is the largest-first fit the delivery asks to beat.
    """
    n_labels = arrays.max_trucks + 1
    n_classes = len(classes)
    model = aggregate(evaluate_model(episodes, arrays, logits, policy, n_classes), n_labels)
    greedy = aggregate(evaluate_greedy(episodes, arrays, n_classes), n_labels)
    return model, greedy


def select_policy(episodes: list, arrays, logits: np.ndarray, n_classes: int) -> str:
    """Choose the decoder policy by validation, on the primary objective."""
    n_labels = arrays.max_trucks + 1
    best, best_gap = "model", float("inf")
    for policy in POLICIES:
        m = aggregate(evaluate_model(episodes, arrays, logits, policy, n_classes), n_labels)
        if m["loaded_gap_mean"] < best_gap:
            best, best_gap = policy, m["loaded_gap_mean"]
    return best
