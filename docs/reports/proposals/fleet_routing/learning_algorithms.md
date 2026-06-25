# Learning‑Based Approaches for Fleet Routing

## Why add a data‑driven model?

While OR‑Tools provides an exact/heuristic solution for a single instance, learning‑based methods offer:

- **Fast “what‑if” predictions** – near‑instant inference for new demand snapshots.
- **Demand forecasting** – a model can ingest historical CSVs and predict future volumes.
- **Warm‑starts for the optimizer** – a Graph Neural Network (GNN) can suggest an initial routing plan that OR‑Tools later refines, reducing solve time.
- **Strategic insights** – clustering, anomaly detection, and feature importance help guide higher‑level decisions (e.g., depot placement).

## Typical workflow

1. **Data preparation** – Load the cleaned CSVs from `data/clean/` and build a demand‑distance matrix.
2. **Model training** – Train a GNN (see `src/models.py` and `scripts/train_gnn.py`) to predict demand clusters / an initial route.
3. **Inference / warm‑start** – For a new demand snapshot run the model (`src/pipeline/inference.py`); the output is a candidate route list.
4. **OR‑Tools refinement** – Feed the candidate as a warm‑start to the `RoutingModel` (see `src/pipeline/cleaning/deduplication.py` or a dedicated `run_optimization.py`).
5. **Visualization** – Export the final routes to the existing visualisation scripts (`visuals/class_distribution.png`, `visuals/geographic_demands.png`, …).

## Code references

- **Model definition** – `src/models.py`
- **Training script** – `scripts/train_gnn.py`
- **Inference wrapper** – `src/pipeline/inference.py`
- **OR‑Tools integration** – `src/pipeline/cleaning/deduplication.py` (function `run_gnn_and_optimize`)

## When to use it

| Situation | Benefit of the ML component |
|-----------|-----------------------------|
| Real‑time dispatch (sub‑second response) | Inference replaces a full OR‑Tools solve. |
| Large fleets (≥ 50 vehicles) | Warm‑starts dramatically cut solver time. |
| Frequently changing demand patterns | Forecast‑driven inputs improve solution quality. |
| Need for strategic insights | Clustering & feature importance inform depot planning. |
