# Fleet Loading

Supervised imitation learning for capacitated fleet loading — assign vehicles to trucks or defer, trained from exhaustive search labels.

## Models

| Model | Accuracy | Defer F1 | Type |
|---|---|---|---|
| **XGBoost** | 95.8% | 0.028 | Per-vehicle tree baseline |
| **LightGBM** | 95.7% | 0.001 | Per-vehicle tree baseline |
| **Transformer** | 78.7% | **0.658** | Set-based (attention over vehicles) |

## Quick start

```bash
cd fleet_loading
source .venv/bin/activate

# Run the full pipeline
kedro run

# Start MLflow UI
# MLflow runs are stored in fleet_loading/mlflow.db (SQLite)
MLFLOW_TRACKING_URI=sqlite:///mlflow.db mlflow ui

# View documentation (from project root)
cd ~/Projects/vehicles && source fleet_loading/.venv/bin/activate && mkdocs serve
```

## Project structure

- `fleet_loading/` — Kedro project with encode → split → train pipeline
- `data/episodes/` — Labeled episodes from exhaustive search teacher
- `reports/` — Method docs and proposals
