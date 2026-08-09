# Operational metrics

The models are judged on the delivery's three formal metrics, computed against
the **exact teacher** in `data/episodes/episodes.parquet`, which carries
`n_loaded` and `cu_utilized` per episode (i.e. `V_exact` for every manifest).
All three models are evaluated on the same held-out validation split (6,968
episodes) via `src/modeling/metrics.py` (the same machinery that evaluates the
MLP), through `fleet_loading/src/fleet_loading/pipelines/training/pairwise.py`.

## The three delivery metrics

1. **Eficiencia de llenado volumétrico** — CU used / total truck capacity
   (`cu_utilization_model_pct`). Fill is capacity-rich by construction, so
   teacher and models converge near ~36%; the discriminating signal is the
   loaded gap below.
2. **Tiempo de cómputo** — milliseconds from manifest to full assignment
   (`latency.mean_ms`, `p99_ms`), measured with `time.perf_counter`.
3. **Brecha óptima** — `(V_teacher − V_model) / V_teacher` on the primary
   objective (vehicles loaded). The teacher is the exact DP, proven equal to
   brute-force enumeration on all instances, so this is the delivery's
   "brecha óptima en instancias acotadas".

## Feasibility invariant

Every plan produced by the decoders is **feasible by construction** — a vehicle
is only placed when it fits in remaining capacity. The hard gate is
`capacity_violation_rate = 0.0`; if it is ever nonzero, the other metrics are
meaningless.

`max_overflow_cu` may be a tiny nonzero float (~1e-7) for the attention model
because its decoder packs in float32 and the report re-checks in float64. Any
overflow below `_TOL = 1e-9` is treated as measurement noise, not a violation.

## Per-episode report (`EpisodeResult`)

Built by `src.modeling.metrics.build_result` from `capacity_decoder.DecodedEpisode`:

| Field | Meaning |
|---|---|
| `episode_id` | manifest id |
| `n_vehicles`, `n_trucks` | manifest size |
| `total_capacity` | Σ truck capacities (CU) |
| `model_n_loaded` | vehicles the model loads |
| `teacher_n_loaded` | vehicles the exact teacher loads (`V_exact`) |
| `model_cu`, `teacher_cu` | CU utilized by model / teacher |
| `max_overflow` | largest over-capacity load (CU) |

## Aggregates (`aggregate`)

| Metric | Formula |
|---|---|
| `capacity_violation_rate` | mean(max_overflow > 1e-9) — must be 0 |
| `loaded_gap_mean` | mean(teacher_n_loaded − model_n_loaded) |
| `episodes_matching_teacher_count_pct` | % episodes where model_n_loaded = teacher_n_loaded |
| `optimality_gap_loaded_pct` | 100 · mean((teacher − model)/teacher) |
| `cu_gap_mean` | mean(teacher_cu − model_cu) |
| `cu_utilization_model_pct` | 100 · Σ model_cu / Σ total_capacity |
| `cu_utilization_teacher_pct` | 100 · Σ teacher_cu / Σ total_capacity |
| `latency.mean_ms / median_ms / p99_ms` | decoder (`decode_episode`) compute time per manifest |

## Baselines

Each model is reported against the **greedy baseline**
(`src.modeling.metrics.evaluate_greedy`, largest-first fit), the manual
heuristic the delivery asks to beat. Results in `docs/index.md` show all learned
models beat greedy on the primary objective by a wide margin (optimality gap
~0.15% vs greedy's 4.49%).

## In MLflow

MLflow stores metrics as flat key-value pairs, so each aggregate is recorded
twice per model — once for the model and once for the greedy baseline — plus
the diagnostic classifier metrics. Key scheme:

```
<model>_<model|greedy>_<aggregate metric>        operational metrics
<model>_val_accuracy                             raw-label accuracy (diagnostic)
<model>_val_defer_f1                             defer F1 on raw labels (diagnostic)
att_cap_accuracy, att_cap_defer_f1               attention, capacity-aware decoder
```

Examples: `xgb_model_optimality_gap_loaded_pct` = the XGBoost model's
optimality gap; `xgb_greedy_latency_mean_ms` = the greedy baseline's mean
compute time; `att_model_capacity_violation_rate` = attention feasibility gate.
Each `<aggregate metric>` name is exactly the key documented in the
[aggregates table](#aggregates-aggregate) above, so the MLflow UI
maps 1:1 onto the formulas here. Note the `latency_*` keys appear individually
(`_mean_ms`, `_median_ms`, `_p99_ms`, `_n_manifests_timed`) rather than nested.

### Training curves (loss vs rounds/epochs)

Curves are logged natively and render as line charts in the MLflow UI. The
GBTs also re-log their curves under unambiguous names (autolog uses the
framework's own eval-set labels, which both call the train split "validation"):

- **XGBoost**: `xgb_train_logloss` / `xgb_train_accuracy_curve` (train),
  `xgb_val_logloss` / `xgb_val_accuracy_curve` (val) — one step per boosting
  round (500). Autolog's `validation_0/1-logloss` are the same loss data under
  XGBoost's naming.
- **LightGBM**: `lgb_train_binary_logloss` / `lgb_train_accuracy_curve`,
  `lgb_val_binary_logloss` / `lgb_val_accuracy_curve` — one step per round until
  early stopping. Autolog's `training/valid_1-binary_logloss` are the same data
  under LightGBM's naming.
- **Attention**: `att_train_loss` / `att_train_accuracy_curve`,
  `att_val_accuracy_curve`, `att_val_defer_f1_curve` — one step per epoch (50).

These come from `mlflow.<framework>.autolog(log_models=False)` (captures the
framework's native `eval_set` results) plus per-epoch `mlflow.log_metric(..., step=epoch)`.

### Confusion matrices

Confusion matrices are **not** produced during training. Training nodes only
emit predictions (`*_predictions.parquet`); the `report_confusion_matrices`
Kedro node renders figures from them into `data/08_reporting/`. All three
models emit predictions in the canonical index space (`0 = Sin camión`, `1..T =
trucks by capacity descending`), so the matrices are `(T+1)`-way with **dynamic
labels** — one column per truck index actually present, never a fixed truck
count:

| Figure | Predictions source |
|---|---|
| `xgb_confusion_matrix_train.png`, `xgb_confusion_matrix_val.png` | `xgb_predictions.parquet` |
| `lgb_confusion_matrix_train.png`, `lgb_confusion_matrix_val.png` | `lgb_predictions.parquet` |
| `att_confusion_matrix_val.png` (capacity-aware decoder) | `att_predictions.parquet` |

Because figures are a pure function of `(y_true, y_pred, labels)`, restyling
them never requires retraining — edit `_confusion_matrix_figure` in `nodes.py`,
then:

```bash
kedro run --nodes report_confusion_matrices
```

The report node also overwrites the `confusion_matrix.png` artifact that
`mlflow.evaluate()` logs with numeric labels: MLflow needs numeric class labels
for its confusion-matrix computation, so training leaves MLflow's plot
untouched, and the report node replaces it with a readable normalized version
in the same run, located via the `run_id` stored in each model's results.
