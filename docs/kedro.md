# Kedro pipeline

## Nodes

| Node | Input | Output | Description |
|---|---|---|---|---|
| `encode` | vehicles, episodes | encoded_vehicles | Merge, add features (iso_week encoding, cross-vehicle aggregates, greedy packing simulation) |
| `split` | encoded_vehicles | train_df, val_df | GroupShuffleSplit by episode_id (80/20) |
| `train_xgboost` | train_df, val_df, episodes | xgb_results, xgb_predictions | XGBoost per-vehicle classifier + operational metrics + predictions |
| `train_lightgbm` | train_df, val_df, episodes | lgb_results, lgb_predictions | LightGBM per-vehicle classifier + operational metrics + predictions |
| `train_attention` | train_df, val_df, episodes | att_results, att_predictions | Transformer encoder over episode vehicle sets + operational metrics + predictions |
| `report_confusion_matrices` | xgb/lgb/att_predictions, xgb/lgb_results | 5 confusion-matrix figures + MLflow overwrite | Pure rendering step: reads cached predictions, writes PNGs to `data/08_reporting/`, and overwrites MLflow's numeric `confusion_matrix.png` with the readable version |

Training nodes only emit **data** (metrics + predictions) to the catalog; they never
render plots. Figures are a pure function of predictions, so restyling them
(axis labels, titles, colormap) means editing `operational.py`'s
`CONFUSION_LABELS` / `nodes.py`'s `_confusion_matrix_figure` and re-running a
single fast node:

```bash
kedro run --nodes report_confusion_matrices
```

This updates both the `data/08_reporting/` PNGs and the `confusion_matrix.png`
artifact in the corresponding MLflow runs (via the `run_id` stored in each
model's results). No retraining needed.

## Parameters

See `conf/base/parameters.yml`. Key params:

- `test_size: 0.2`
- `attention.d_model: 64` — embedding dimension
- `attention.n_epochs: 50`
- `xgboost.scale_pos_weight: 200`
- `lightgbm.scale_pos_weight: 50`

## Running

```bash
cd fleet_loading
source .venv/bin/activate
kedro run
```

Results are written to `data/07_model_output/` and tracked in MLflow.
