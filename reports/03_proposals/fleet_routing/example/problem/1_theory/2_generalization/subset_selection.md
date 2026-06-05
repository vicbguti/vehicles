# Subset Selection Generalization

This document provides the generalized algebraic formulation for the pure subset selection search space (the Multidimensional Knapsack Problem) when the optimal delivery size $N$ is unknown and must be solved as a proper subset of the total candidate pool.

---

## 1. Selection Space (Proper Subsets)
Before routing is considered, the selection step alone requires choosing a subset $S$ of vehicles from the candidate pool $\mathcal{M}$ (where $M = |\mathcal{M}|$). 

Because the size of the total candidate pool $M$ exceeds the capacity limit of the fleet, the selected subset $S$ must be a **non-empty proper subset** of $\mathcal{M}$ (i.e., we must deliver at least 1 vehicle, and we cannot deliver all $M$ vehicles):
* $\emptyset \subset S \subsetneq \mathcal{M}$

The number of possible candidate subsets to evaluate is given by the formula for non-empty proper subsets:
$$\text{Selection Space} = 2^M - 2$$


---

## 2. Complexity Classification
This generalization proves that the selection space size is bounded by:
$$\mathcal{O}(2^M)$$

This represents exponential growth, confirming that even before considering the factorial complexity of routing sequences, the subset selection phase (modeled as a Multidimensional Knapsack Problem) is NP-hard and mathematically intractable to solve optimally via exhaustive search as $M$ scales.


