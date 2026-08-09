# Kedro pipeline

## Nodes

| Node | Input | Output | Description |
|---|---|---|---|
| `encode` | vehicles, episodes | encoded_vehicles | Join vehicles + episodes, keep the teacher columns the pairwise tensors need (`truck_capacities`, `n_loaded`, `cu_utilized`), drop non-optimal episodes. No feature engineering: the models consume the canonical `src/modeling` pairwise tensors. |
| `split` | encoded_vehicles | train_df, val_df | GroupShuffleSplit by episode_id (80/20) |
| `train_xgboost` | train_df, val_df, episodes | xgb_results, xgb_predictions | XGBoost binary **pairwise** classifier (one row per `(vehicle, truck)` option + defer) + capacity-aware decode + operational metrics + predictions |
| `train_lightgbm` | train_df, val_df, episodes | lgb_results, lgb_predictions | LightGBM binary pairwise classifier, same contract |
| `train_attention` | train_df, val_df, episodes | att_results, att_predictions | Transformer encoder over episode vehicle sets with a pairwise `(vehicle, truck)` head + defer head; dynamic truck axis |
| `report_confusion_matrices` | xgb/lgb/att_predictions, xgb/lgb_results | 5 confusion-matrix figures + MLflow overwrite | Pure rendering step: reads cached predictions, writes PNGs to `data/08_reporting/`, and overwrites MLflow's numeric `confusion_matrix.png` with the readable version |

Training nodes only emit **data** (metrics + predictions) to the catalog; they never
render plots. Figures are a pure function of predictions, so restyling them
(axis labels, titles, colormap) means editing `_confusion_matrix_figure` in
`nodes.py` and re-running a single fast node:

```bash
kedro run --nodes report_confusion_matrices
```

This updates both the `data/08_reporting/` PNGs and the `confusion_matrix.png`
artifact in the corresponding MLflow runs (via the `run_id` stored in each
model's results). No retraining needed.

## The pairwise design (why no truck count is baked in)

All three models emit per-episode logits `(V, 1 + T)` in the canonical index
space (`0 = SIN_CAMION`, `1..T = trucks by capacity descending`) and are decoded
with `src.modeling.capacity_decoder.decode_episode`, whose truck axis is `None`.
This is what makes the models work with **any** number of trucks — including the
5–10 extrapolation tests (see `docs/index.md` and
`scripts/evaluate_fleet_loading.py`). The shared machinery lives in
`pipelines/training/pairwise.py`:

- `build_tensors` — `src.modeling.features.build_all_episodes` + `BlockScaler`
  (fit on train only) + `build_model_arrays`.
- `option_rows` / `logits_from_proba` — the GBT view: a binary `is_chosen`
  classifier over `(vehicle, truck)` options with an explicit `is_defer` flag.
- `evaluate_split` / `select_policy` / `measure_latency` — decoder policy choice
  by validation `loaded_gap_mean`, episode aggregates vs teacher and greedy
  baseline, and decoder latency, all via `src.modeling.metrics`.

## Parameters

See `conf/base/parameters.yml`. Key params:

- `test_size: 0.2`
- `attention.d_model: 64` — embedding dimension
- `attention.n_epochs: 50`
- `xgboost.*`, `lightgbm.*` — GBT hyperparameters (`scale_pos_weight` is accepted
  for signature compatibility but the pairwise binary classifier uses balanced
  per-class sample weights instead)

## Running

```bash
cd fleet_loading
source .venv/bin/activate
kedro run
```

Results are written to `data/07_model_output/` and tracked in MLflow. Trained
models + preprocessing schemas are also saved under
`artifacts/fleet_loading/<model>/` (classifier + `pairwise_schema.json`) for the
extrapolation evaluator.
