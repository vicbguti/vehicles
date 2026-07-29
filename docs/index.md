# Fleet Loading

Supervised imitation learning for capacitated fleet loading — assign vehicles to trucks or defer, trained from exhaustive search labels.

## Models

| Model | Accuracy | Defer F1 | Type |
|---|---|---|---|
| **XGBoost** | 95.8% | 0.029 | Per-vehicle tree baseline |
| **LightGBM** | 95.7% | 0.001 | Per-vehicle tree baseline |
| **Transformer** | 81.2% | **0.662** | Set-based (attention over vehicles) |

## Quick start

```bash
cd fleet_loading
source .venv/bin/activate

# Run the full pipeline
kedro run

# Start MLflow UI
mlflow ui

# View documentation (from project root)
cd ~/Projects/vehicles && source fleet_loading/.venv/bin/activate && mkdocs serve
```

## Project structure

- `fleet_loading/` — Kedro project with encode → split → train pipeline
- `data/episodes/` — Labeled episodes from exhaustive search teacher
- `reports/` — Method docs and proposals
