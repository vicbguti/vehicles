# Subset Selection Application (18-Vehicle Scenario)

This document details the selection combinations of the candidate vehicle pool to find the optimal cargo subset.

---

## 1. Concrete Selection Space
In our scenario, we have a total pool of **$M = 18$ vehicles** available at the port. To find the optimal delivery cargo, the solver must evaluate combinations across all possible subset sizes ($S = 1, 2, \dots, 18$):

$$\text{Total Subsets to Evaluate} = \sum_{S=1}^{18} \binom{18}{S} = 2^{18} - 1 = \mathbf{262,143 \text{ combinations}}$$

---

## 2. Decoupling from Feasibility
To find the maximum deliverable cargo, the solver searches through these subset combinations (starting from size 18 down to 1). For each generated subset, the solver must perform a separate feasibility check to verify if the subset can be physically packed into the trucks. 

The mathematical proof of why subsets of sizes 18, 17, and 16 are infeasible, and how size 15 is determined to be the maximum partitionable subset, is detailed in [bin_packing.md](./bin_packing.md).

