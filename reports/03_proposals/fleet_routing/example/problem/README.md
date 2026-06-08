# Problem Definition Index

This directory contains the constraints, manual baseline methodologies, and mathematical limits of the fleet routing problem.

## 📋 Parameters & Constraints
* [scenario.md](./scenario.md) — The distribution scenario setup (available vehicles, capacities, and destinations).
* [constraints.md](./constraints.md) — Vehicle class dimensions and Capacity Unit (CU) assignments.
* [failures.md](./failures.md) — Comparative analysis of Case 1 vs. Case 2 heuristic failure modes.

## 📂 Sub-Directories

### [1. Mathematical Theory & Computational Limits](./1_theory/README.md)
General mathematical bounds of the search space:
* [complexity.md](./1_theory/1_search_space/complexity.md) — Combinatorial math of the routing search space.
* [intractability.md](./1_theory/1_search_space/intractability.md) — Mathematical scaling and intractability.
* [subset_selection.md](./1_theory/1_search_space/subset_selection.md) — Concrete application of subset selection for the 18-vehicle scenario.
* [subset_selection.md](./1_theory/2_generalization/subset_selection.md) — Generalized algebraic formulation for variable N.
* [formulation.md](./1_theory/2_generalization/formulation.md) — Generalized algebraic formulation and cancellation proof.
* [limits.md](./1_theory/3_compute_limits/limits.md) — Comparison of search space times with supercomputers.




### [2. Greedy Heuristics Failures](./2_greedy)
* [greedy.md](./2_greedy/greedy.md) — Case 2: Analysis of why nearest-neighbor routing fails (backtracking).

### [3. Manual Status Quo](./3_status_quo)
* [status_quo.md](./3_status_quo/status_quo.md) — Case 1: Human-dispatcher manually planned route layout and inefficiencies.
