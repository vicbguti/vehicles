# Generalized Capacity Bounds

This document provides the generalized algebraic formulation for determining the theoretical mathematical bounds (minimum and maximum counts) of different vehicle classes in any selected subset of size $N$ that satisfies a total fleet capacity limit.

---

## 1. Mathematical Formulation
Let the selected subset contain vehicles belonging to $P$ distinct classes, where:
* $w_k$ = Capacity Unit (CU) weight of a vehicle in class $k$ (ordered such that $w_1 < w_2 < \dots < w_P$)
* $n_k$ = number of vehicles of class $k$ selected for the delivery subset
* $N$ = total size of the selected subset, where $\sum_{k=1}^P n_k = N$
* $C_{\text{total}}$ = total capacity of the carrier fleet

To be feasible, the selection must satisfy the total capacity constraint:
$$\sum_{k=1}^P w_k n_k \le C_{\text{total}}$$

---

## 2. Derivation of Bounds for Two Vehicle Classes ($P = 2$)
When there are only two classes of vehicles (e.g., lightweight class with weight $w_1$ and heavyweight class with weight $w_2$, where $w_1 < w_2$):

1. **Size Relation**:
   $$n_1 + n_2 = N \implies n_1 = N - n_2$$

2. **Capacity Inequality**:
   $$w_1 n_1 + w_2 n_2 \le C_{\text{total}}$$

3. **Heavyweight Upper Bound ($n_2$)**:
   Substitute $n_1 = N - n_2$ into the capacity inequality:
   $$w_1(N - n_2) + w_2 n_2 \le C_{\text{total}}$$
   $$w_1 N + (w_2 - w_1)n_2 \le C_{\text{total}}$$
   $$(w_2 - w_1)n_2 \le C_{\text{total}} - w_1 N$$

   Since $w_2 > w_1$, the term $(w_2 - w_1)$ is positive. Dividing both sides gives the upper bound on the heavyweight class:
   $$n_2 \le \frac{C_{\text{total}} - w_1 N}{w_2 - w_1}$$

4. **Lightweight Lower Bound ($n_1$)**:
   Conversely, since $n_2 = N - n_1$, substituting this into the capacity inequality yields:
   $$w_1 n_1 + w_2(N - n_1) \le C_{\text{total}}$$
   $$w_2 N - (w_2 - w_1)n_1 \le C_{\text{total}}$$
   $$(w_2 - w_1)n_1 \ge w_2 N - C_{\text{total}}$$

   Dividing by the positive term $(w_2 - w_1)$ gives the lower bound on the lightweight class:
   $$n_1 \ge \frac{w_2 N - C_{\text{total}}}{w_2 - w_1}$$

---

## 3. Generalization to $P > 2$ Classes
For $P$ classes, the boundaries for class $k$ ($n_k$) are bounded by the extreme scenarios where all other selected vehicles are chosen from either the lightest class ($1$) or the heaviest class ($P$):

* **Upper Bound for Class $k$** (assuming all other selected vehicles belong to the lightest class $w_1$):
  $$n_k \le \frac{C_{\text{total}} - w_1 N}{w_k - w_1} \quad (\forall k > 1)$$

* **Lower Bound for Class $k$** (assuming all other selected vehicles belong to the heaviest class $w_P$):
  $$n_k \ge \frac{w_P N - C_{\text{total}}}{w_P - w_k} \quad (\forall k < P)$$
