# Feasibility of Subset Sizes

This document evaluates candidate vehicle subsets in descending order of size to find the absolute maximum size that can physically fit within the fleet capacity.

---

## 1. Subset Size Checks
Using the parameters defined in [1_scenario_parameters.md](./1_scenario_parameters.md), the solver evaluates generated subsets starting from the maximum size of the pool:

1. **Subsets of Size 18 (All vehicles)**:
   * Total CUs: 14.0 CUs.
   * *Result*: **Infeasible**. Exceeds total fleet capacity of 12.0 CUs.
2. **Subsets of Size 17**:
   * Minimum possible CUs (selecting all 12 Sedans + 5 SUVs): $(12 \times \frac{2}{3}) + (5 \times 1.0) = 8.0 + 5.0 = \mathbf{13.0 \text{ CUs}}$.
   * *Result*: **Infeasible**. Every combination exceeds the 12.0 CU limit and fails.
3. **Subsets of Size 16**:
   * Minimum possible CUs (selecting all 12 Sedans + 4 SUVs): $(12 \times \frac{2}{3}) + (4 \times 1.0) = 8.0 + 4.0 = \mathbf{12.0 \text{ CUs}}$.
   * *Result*: **Feasible**. Partitions matching the total capacity limit exist.

---

## 2. Conclusion
The largest possible subset size that can satisfy the capacity limits of the fleet is **$N = 16$**. Any larger selection of vehicles is mathematically impossible to deliver.
