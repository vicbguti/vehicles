# Solver Search Walkthrough (Pruning Example)

This document provides a concrete walkthrough of how the backtracking search tree and capacity pruning (detailed in [matrix_search.md](../2_generalization/3_partitioning/matrix_search.md)) operate on our specific 16-vehicle scenario.

---

## 1. Search Setup
We are partitioning the 16 selected vehicles (4 SUVs and 12 Sedans) between $K = 2$ carrier trucks of capacity $C = 6.0\text{ CUs}$ each:
* **SUVs** ($w_{\text{SUV}} = 1.0\text{ CU}$)
* **Sedans** ($w_{\text{Sedan}} = \frac{2}{3}\text{ CU}$)

The solver assigns these 16 vehicles to the trucks one-by-one, building the $2 \times 16$ assignment matrix column-by-column.

---

## 2. Walkthrough of a Pruned Search Branch
Let's trace a branch of the decision tree where the solver attempts to assign too many Sedans to Truck 1:

1. **Step 1 to 9**: The solver assigns 9 Sedans to Truck 1.
   * *Weight on Truck 1*: $9 \times \frac{2}{3} = \mathbf{6.0\text{ CUs}}$
   * *Status*: Feasible (Truck 1 is exactly at 100% capacity).
2. **Step 10**: The solver attempts to assign the 10th Sedan to Truck 1.
   * *Weight on Truck 1*: $10 \times \frac{2}{3} = \mathbf{6.67\text{ CUs}}$
   * *Status*: **Infeasible**. Exceeds Truck 1's capacity of 6.0 CUs.

### The Pruning Action
Because Truck 1 is already over capacity at Step 10:
* The solver **does not** proceed to assign the 11th and 12th Sedans.
* The solver **does not** proceed to assign the 4 SUVs.
* It immediately **prunes** this entire branch of the search tree, backtracks to the decision at Step 9, and assigns the 10th Sedan to Truck 2 instead.

---

## 3. Computational Impact
A naive, brute-force search would evaluate all possible distributions of 16 distinct vehicles to 2 trucks:
$$\text{Brute Force Space} = 2^{16} = \mathbf{65,536 \text{ assignments}}$$

By incrementally checking constraints and pruning branches as soon as a single truck goes over capacity, the solver only has to evaluate a tiny fraction of the $65,536$ combinations to find the 3 valid configuration splits.
