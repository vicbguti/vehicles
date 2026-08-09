# Fleet Loading

Supervised imitation learning for capacitated fleet loading — assign vehicles to trucks or defer, trained from exhaustive search labels.

## Models

Per-vehicle **per-truck** classification (CAMION_1..4 + defer) on the raw labels, and the **operational metrics** from `operational.py` (evaluated on the full held-out val split, 6,968 episodes) that the delivery specifies: fill efficiency, compute ms, and the gap vs the exact teacher (`n_loaded` per episode in `episodes.parquet`). All three models predict which truck each vehicle goes on (or defer) and decode capacity-aware; Greedy = largest-first pack baseline. All plans are feasible by construction (`capacity_violation_rate = 0.0` for every model).

| Model | Accuracy | Defer F1 | Opt. gap (veh) | Matches teacher | Fill (CU) | Compute (mean/p99 ms) |
|---|---|---|---|---|---|---|
| **XGBoost** | 76.5% | 0.616 | 0.24% | 96.6% | 35.93% | 30.5 / 56.3 |
| **LightGBM** | 77.9% | 0.614 | 0.33% | 96.3% | 35.97% | 17.4 / 35.3 |
| **Transformer** | **78.7%** | **0.664** | 4.64% | 86.2% | **36.30%** | **3.55 / 4.1** |
| Greedy baseline | — | — | 4.49% | 87.2% | **36.40%** | 0.02 / 0.04 |

Notes:

- **Per-truck accuracy** (all models, raw labels) is now comparable: attention leads at ~78-79%, the GBTs at ~77%. The old binary "95.8%" was inflated by predicting the majority `loaded` class; the per-truck task is genuinely harder and is what the problem specifies (`docs/proposals/04_method.md`).
- **Optimality gap** = `(V_teacher − V_model)/V_teacher` on the primary objective (vehicles loaded). The teacher is the exact DP = brute-force optimum on all 34,839 episodes, so this is the delivery's "brecha óptima en instancias acotadas".
- **Fill efficiency** is capped at ~36% because episodes are capacity-rich (more truck capacity than CU demand — see `docs/proposals/09_scenarios_coverage.md`); teacher and all models converge near the same value, so the discriminating metric is the loaded-gap.
- **Compute** is the full manifest→assignment latency in ms (`time.perf_counter`). Greedy is a linear-time baseline; the Transformer is fastest among the learned models thanks to batched inference.
- On the primary objective the GBTs beat the teacher on a fraction of episodes (they load as many as fit; the exact teacher's lexicographic tie-break on identical vehicles is unlearnable) and sit ~0.2% below it in aggregate; attention trades some optimality for the fastest latency and the best per-truck accuracy.

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
