# Fleet Loading

Supervised imitation learning for capacitated fleet loading — assign vehicles to trucks or defer, trained from exhaustive search labels.

## Models

All three models are **pairwise**: they score every `(vehicle, truck)` option plus a defer option and decode with a capacity-respecting decoder, so the truck axis is fully dynamic (any number of trucks, including the 5–10 used in extrapolation tests). They share the canonical `src/modeling` feature tensors and evaluation machinery. Operational metrics are computed against the exact teacher on the held-out val split (6,968 episodes, GroupShuffleSplit by episode_id): fill efficiency, compute ms, and the gap vs the teacher's `n_loaded`. Greedy = largest-first pack baseline. All plans are feasible by construction (`capacity_violation_rate = 0.0` for every model).

| Model | Per-vehicle acc (decoded) | Defer F1 | Opt. gap (veh) | Matches teacher | Fill (CU) | Compute (mean/p99 ms) |
|---|---|---|---|---|---|---|
| **XGBoost** | 81.0% | 0.625 | 0.15% | 97.5% | 35.82% | 0.07 / 0.15 |
| **LightGBM** | 80.9% | 0.625 | 0.15% | 97.5% | 35.82% | 0.07 / 0.15 |
| **Transformer** | **82.1%** | **0.703** | 0.16% | 97.4% | **35.82%** | **0.08 / 0.16** |
| Greedy baseline | — | — | 4.49% | ~87% | 36.40% | 0.02 / 0.04 |

Notes:

- **Per-vehicle accuracy** (all models, capacity-aware decoded labels) is 81–82%; attention's raw-label val accuracy is 84.6%. The greedy baseline's raw per-vehicle accuracy is ~0.21 on the held-out split.
- **Optimality gap** = `(V_teacher − V_model)/V_teacher` on the primary objective (vehicles loaded). The teacher is the exact DP = brute-force optimum on all 34,839 episodes, so this is the delivery's "brecha óptima en instancias acotadas". All three models now land at ~0.15% — two orders of magnitude closer to the teacher than greedy (4.49%) and a large improvement over the previous per-truck formulation (0.24–4.64%).
- **Extrapolation beyond training (5–10 trucks):** each model was evaluated on re-labeled manifests with larger fleets (see `scripts/evaluate_fleet_loading.py`). With 5–6 trucks at the same per-truck capacity distribution, all three models match the teacher's `n_loaded` on **100%** of episodes. In the hard scenario (8–10 trucks, total capacity held constant), the models stay at ~98.3–98.6% teacher-matching (XGB 98.4%, LGB 98.3%, attention 98.6%) with zero capacity violations — the pairwise structure generalizes beyond the `1–4` trucks seen in training.
- **Compute** is the decoder latency in ms (`decode_episode` only, shared step; score assembly is model-specific). All three learned models decode a manifest in <0.1 ms median — far below the greedy baseline's 0.02 ms but all well within interactive bounds. (Greedy's raw-accuracy/fill columns above are from the pre-pairwise report; its decoder latency is 0.02/0.04 ms.)
- **Fill efficiency** is capped at ~36% because episodes are capacity-rich (more truck capacity than CU demand — see `docs/propuesta/09_scenarios_coverage.md`); teacher and all models converge near the same value, so the discriminating metric is the loaded-gap.

## Extrapolation results

All three models evaluated on re-labeled manifests with fleets larger than the training range (1–4 trucks); `loaded_gap_mean` = mean(teacher − model vehicles loaded):

| Set (trucks, capacity mode) | XGBoost | LightGBM | Attention | Greedy |
|---|---|---|---|---|
| 5–6, same distribution | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 8–10, constant total | 0.0274 | 0.0294 | 0.0209 | 0.0157 |

Per-model JSON with full aggregates: `artifacts/fleet_loading/<model>/extrap_*_metrics.json`.

## Quick start

Desde la raíz del repositorio. No hace falta ningún entorno virtual por
subproyecto: hay un solo `pyproject.toml` y un solo `uv.lock`.

```bash
# 1. Entorno y datos. El paso de LFS no es opcional: sin él los CSV son
#    punteros de 133 bytes y el pipeline procesa basura en silencio.
uv sync
git lfs install --local && git lfs pull

# 2. Datos derivados (el barrido completo de episodios tarda ~30 min;
#    usa --limit para una muestra)
uv run python scripts/build_vehicle_features.py
uv run python scripts/build_scenarios.py --limit 200

# 3. Entrenar y evaluar el MLP
uv run python scripts/train_mlp.py
uv run python scripts/evaluate_mlp.py

# 4. Los otros tres modelos (pipeline Kedro). Necesitan sus extras:
uv sync --extra gbt --extra attention --extra tracking --extra kedro
cd fleet_loading && uv run kedro run

# 5. MLflow (la base está en la raíz del repo, mlflow.db)
uv run --extra tracking mlflow ui --backend-store-uri sqlite:///mlflow.db

# 6. Documentación
uv run --extra docs mkdocs serve
```

Con `just` instalado, `just setup` hace el paso 1 y deja los hooks activos.

## Project structure

- `fleet_loading/` — Kedro project with encode → split → train pipeline
- `data/episodes/` — Labeled episodes from exhaustive search teacher
- `reports/` — Method docs and proposals
