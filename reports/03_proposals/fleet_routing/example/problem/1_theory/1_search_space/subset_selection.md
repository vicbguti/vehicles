# Subset Selection Application (18-Vehicle Scenario)

This document details the concrete application of the subset selection check (Knapsack Problem) to find the maximum deliverable cargo for the 18-vehicle shipment scenario.

---

## 1. Concrete Selection Space
In our scenario, we have a total pool of **$M = 18$ vehicles** available at the port. To determine the maximum number of vehicles that can fit into the two 6.0 CU trucks, the solver must evaluate subsets of all possible sizes ($S = 1, 2, \dots, 18$):

$$\text{Total Subsets to Evaluate} = \sum_{S=1}^{18} \binom{18}{S} = 2^{18} - 1 = \mathbf{262,143 \text{ combinations}}$$

For each subset, the solver must run a capacity bin-packing check to see if it can be partitioned into the trucks.

---

## 2. Iterative Verification Steps
To mathematically verify that **15** is the absolute maximum feasible delivery volume, the solver searches in descending order of size:

1. **Subsets of Size 18 (All vehicles)**:
   * Combinations: $\binom{18}{18} = 1$ combination.
   * *Result*: Fails capacity check (12.06 CUs > 12.0 CUs limit).
2. **Subsets of Size 17**:
   * Combinations: $\binom{18}{17} = 18$ combinations.
   * *Result*: All 18 combinations fail capacity check.
3. **Subsets of Size 16**:
   * Combinations: $\binom{18}{16} = 153$ combinations.
   * *Result*: All 153 combinations fail capacity check.
4. **Subsets of Size 15**:
   * Combinations: $\binom{18}{15} = 816$ combinations.
   * *Result*: Finds a feasible grouping (6 SUVs + 9 Sedans = 12.03 CUs, matching the threshold limit).

Only after checking these **988 combinations** ($1 + 18 + 153 + 816$) does the solver mathematically establish that 15 is the optimal subset size.
