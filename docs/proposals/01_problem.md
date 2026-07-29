# Problem

## Real-world context

Car distributors in Ecuador deliver newly imported or assembled vehicles to dealerships across **221 cantons**. Dispatch must respect:

* **Capacity limits** — car-carrier payload and deck space per truck.
* **Heterogeneous vehicles** — SUVs, sedans, and heavier classes consume different space.
* **Operational cost** — poor loading leaves vehicles behind, forces extra truck rentals, and wastes fleet capacity.

## Project focus: fleet loading

We scope to **capacitated fleet loading**: given a daily manifest of vehicles, decide **which truck carries each vehicle** (or defer to a later shift). **Route sequencing** (visit order, distance) is deferred — see [deferred/](./deferred/).

## Capacity Units (CUs)

Truck capacity and vehicle size are normalized into **Capacity Units**:

| Rule | Value |
|------|-------|
| Truck capacity | **6.0 CU** per carrier |
| SUV | **1.0 CU** (max 6 per truck) |
| Sedan | **0.67 CU** (max 9 per truck) |

Exceeding 6.0 CU on a truck is infeasible.

Formal bin-packing constraints: [deferred/theory/2_generalization/3_partitioning/bin_packing.md](./deferred/theory/2_generalization/3_partitioning/bin_packing.md).

## Why this matters

Manual dispatch often groups by rough region without optimizing **how vehicles pack onto trucks**. That leaves trucks half-empty and pushes vehicles to third-party carriers. The toy case study in [05_evaluation.md](./05_evaluation.md) shows 6 leftovers under status quo vs 2 under optimal loading.
