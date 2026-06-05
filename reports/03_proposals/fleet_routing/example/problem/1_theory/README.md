# Mathematical Theory & Computational Limits Index

This directory contains the theoretical mathematical formulations, combinatorial search space calculations, and physical execution limits of the fleet routing problem.

## 📂 Sub-Directories

### 1. [Search Space](./1_search_space)
Combinatorial search space analysis and scaling:
* [complexity.md](./1_search_space/complexity.md) — Base combinatorial search space math for the 18-vehicle scenario.
* [intractability.md](./1_search_space/intractability.md) — Mathematical scaling and intractability limits.
* [subset_selection.md](./1_search_space/subset_selection.md) — Concrete application of subset selection (262k subsets).
* [bin_packing.md](./1_search_space/bin_packing.md) — Concrete feasibility and bin-packing capacity proof for the 18-vehicle scenario.

### 2. [Generalization](./2_generalization)
Formal algebraic generalizations:
* [formulation.md](./2_generalization/formulation.md) — Generalized algebraic formulation and cancellation proof for fixed N.
* [subset_selection.md](./2_generalization/subset_selection.md) — Generalized algebraic formulation for variable N (pure selection space).
* [bin_packing.md](./2_generalization/bin_packing.md) — Generalized algebraic formulation of the partitioning/bin-packing constraints.

### 3. [Compute Limits](./3_compute_limits)
Physical execution limitations:
* [limits.md](./3_compute_limits/limits.md) — Execution times compared to supercomputers and global compute capacities.

