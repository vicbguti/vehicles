# Problem Definition Index

This directory contains the constraints, manual baseline methodologies, and mathematical limits of the fleet routing problem.

## 📋 Parameters & Constraints
* [scenario.md](./scenario.md) — The distribution scenario setup (available vehicles, capacities, and destinations).
* [constraints.md](./constraints.md) — Vehicle class dimensions and Capacity Unit (CU) assignments.
* [failures.md](./failures.md) — Comparative analysis of Case 1 vs. Case 2 heuristic failure modes.

## 📂 Sub-Directories

### [1. Mathematical Theory & Computational Limits](./1_theory)
General mathematical bounds of the search space:
* [complexity.md](./1_theory/complexity.md) — Combinatorial math of the routing search space.
* [intractability.md](./1_theory/intractability.md) — Mathematical scaling and intractability.
* [limits.md](./1_theory/limits.md) — Comparison of search space times with supercomputers and global compute limits.
* [formulation.md](./1_theory/formulation.md) — Generalized algebraic formulation and cancellation proof.

### [2. Greedy Heuristics Failures](./2_greedy)
* [greedy.md](./2_greedy/greedy.md) — Case 2: Analysis of why nearest-neighbor routing fails (backtracking).

### [3. Manual Status Quo](./3_status_quo)
* [status_quo.md](./3_status_quo/status_quo.md) — Case 1: Human-dispatcher manually planned route layout and inefficiencies.
