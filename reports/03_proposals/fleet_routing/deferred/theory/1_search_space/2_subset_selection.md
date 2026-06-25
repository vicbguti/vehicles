# Subset Selection Space

This document details the selection combinations of the candidate vehicle pool to find the optimal cargo subset.

---

## 1. Concrete Selection Space
In our scenario, we have a total pool of **$M = 18$ vehicles** available at the port (see [1_scenario_parameters.md](./1_scenario_parameters.md)). To find the optimal delivery cargo, the solver must evaluate combinations across all possible subset sizes ($k = 1, 2, \dots, 18$):

$$\text{Total Subsets to Evaluate} = \sum_{k=1}^{18} \binom{18}{k} = 2^{18} - 1 = \mathbf{262,143 \text{ combinations}}$$

---

## 2. Decoupling from Feasibility
To find the maximum deliverable cargo, the solver searches through these subset combinations (starting from size 18 down to 1). For each generated subset, the solver must perform a separate feasibility check to verify if the subset's total volume can be physically packed into the trucks. 

The mathematical proof of why subsets of sizes 18 and 17 are infeasible, and how size 16 is determined to be the maximum partitionable subset, is detailed in [3_capacity_constraints.md](./3_capacity_constraints.md) and [4_bin_packing.md](./4_bin_packing.md).
