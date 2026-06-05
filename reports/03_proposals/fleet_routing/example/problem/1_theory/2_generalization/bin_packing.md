# Bin Packing Generalization

This document provides the generalized algebraic formulation for the fleet partitioning constraints (the Bin Packing Problem) when distributing selected cargo onto carrier trucks.

---

## 1. Mathematical Formulation
Let the partitioning variables be defined as:
* $\mathcal{M}$ = set of available candidate vehicles (where $M = |\mathcal{M}|$)
* $S$ = the selected subset of vehicles ($\emptyset \subset S \subsetneq \mathcal{M}$)
* $N = |S|$ = number of selected vehicles to deliver
* $K$ = number of available carrier trucks
* $C_i$ = Capacity Unit (CU) limit of truck $i$
* $w_j$ = Capacity Unit (CU) weight of vehicle $j \in S$


We define the binary decision variable $x_{ij} \in \{0, 1\}$, where:
$$x_{ij} = \begin{cases} 1 & \text{if vehicle } j \text{ is assigned to truck } i \\ 0 & \text{otherwise} \end{cases}$$

---

## 2. Partitioning Constraints
A selection subset $S$ is mathematically **feasible** if and only if there exists a binary assignment matrix $x$ that satisfies the following conditions:

### A. Unique Assignment
Each selected vehicle must be assigned to exactly one carrier truck:
$$\sum_{i=1}^K x_{ij} = 1 \quad \forall j \in S$$

### B. Capacity Limit
The sum of vehicle capacity units on any single truck cannot exceed its maximum rating:
$$\sum_{j \in S} w_j x_{ij} \le C_i \quad \forall i \in \{1, \dots, K\}$$

---

## 3. Complexity Classification
The decision version of the Bin Packing Problem is NP-complete. Finding a valid assignment $x_{ij}$ for a given subset $S$ requires solving a constraint satisfaction problem whose search space scales as:
$$\mathcal{O}(K^{|S|})$$

This confirms that validating a candidate subset is itself computationally difficult, adding to the exponential complexity of the initial subset selection phase.
