# Evaluation

## Objective (what we optimize)

Given a manifest and fleet (e.g. 2 × 6.0 CU):

* **Maximize** vehicles shipped and CU utilization.
* **Minimize** deferred (leftover) vehicles.
* All assignments **feasible** under capacity.

**Not evaluated:** route order or total km (deferred).

---

## Metrics

| Metric | Description |
|--------|-------------|
| Assignment accuracy | % vehicles matching teacher label (small N) |
| CU utilization | Loaded CU / available fleet CU |
| Leftover count | Vehicles deferred per episode |
| Optimality gap | vs exhaustive teacher (small N) or vs timed search (large N) |
| Inference time | ms per manifest |

---

## Methods compared

| Method | Role |
|--------|------|
| Exhaustive labeler | Optimal reference (small N; timed cap on large N) |
| Status quo | Human-style regional grouping |
| Greedy | First-fit heuristic |
| **Trained assigner** | Primary deliverable |

---

## Toy scenario case study

Documented daily task: **18 vehicles**, **5 cantons**, **2 trucks** × 6 CU — see [example/problem/scenario.md](./example/problem/scenario.md).

**Comparison table** ([example/solution/comparisons.md](./example/solution/comparisons.md)) — for this project, prioritize **grouping, CU load, leftovers**; route/distance columns are illustrative only.

| Case | Leftovers | Truck utilization |
|------|-----------|-------------------|
| 1. Status quo | 6 vehicles | 5.0 / 6.0 CU per truck |
| 2. Greedy | 6 vehicles | 4.0 and 6.0 CU |
| 3. Optimal loading | 2 vehicles | 6.0 / 6.0 CU both trucks |

Detail pages: [status_quo](./example/problem/3_status_quo/status_quo.md) · [greedy](./example/problem/2_greedy/greedy.md) · [optimized](./example/solution/4_optimized/optimized.md)

Use this scenario to **sanity-check** the exhaustive labeler before training.

---

## Planned experiments

1. **Temporal holdout** — train on 2017–2024, evaluate on 2025–2026 weeks.
2. **Size sweep** — N = 10, 20, 30, 50; plot greedy vs model vs timed exhaustive.
3. **Toy replication** — labeler reproduces Case 3 grouping from case study.

---

## Results

*(To be filled after `scripts/eval_loading.py` runs.)*
