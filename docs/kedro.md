# Kedro pipeline

## Nodes

| Node | Input | Output | Description |
|---|---|---|---|
| `encode` | vehicles, episodes | encoded_vehicles | Merge, add features (iso_week encoding, cross-vehicle aggregates, greedy packing simulation) |
| `split` | encoded_vehicles | train_df, val_df | GroupShuffleSplit by episode_id (80/20) |
| `train_xgboost` | train_df, val_df | xgb_results | XGBoost per-vehicle classifier |
| `train_lightgbm` | train_df, val_df | lgb_results | LightGBM per-vehicle classifier |
| `train_attention` | train_df, val_df, episodes | att_results | Transformer encoder over episode vehicle sets |

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
