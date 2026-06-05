# Generalized Selection Intervals (Pool Intersection)

This document details how the theoretical capacity bounds derived in [capacity_bounds.md](./capacity_bounds.md) are intersected with real-world candidate availability constraints to define the actual range of vehicles that can be selected from each class.

---

## 1. Intersection of Constraints
While the capacity bounds define what the fleet can physically carry, the candidate pool defines what is physically available to load.

Let $M_p$ be the number of available candidate vehicles of class $p$ in the port pool. The selected count $n_p$ must satisfy:
1. **Capacity Limit bounds** ($L_p \le n_p \le U_p$) derived in [capacity_bounds.md](./capacity_bounds.md).
2. **Availability limits** ($0 \le n_p \le M_p$).

To satisfy both constraints simultaneously, the selection quantity $n_p$ must lie within the intersection of these intervals:

$$\max\left(0, L_p\right) \le n_p \le \min\left(M_p, U_p\right)$$

---

## 2. General Formulation for $P$ Classes
For any class $p \in \{1, \dots, P\}$, the final selection boundaries are:

* **Lower selection bound ($n_{p,\min}$)**:
  $$n_{p,\min} = \max\left(0, \frac{w_P N - C_{\text{total}}}{w_P - w_p}\right) \quad (\text{for } p < P)$$
  *(with $n_{P,\min} = 0$ as the default boundary if not otherwise bounded).*

* **Upper selection bound ($n_{p,\max}$)**:
  $$n_{p,\max} = \min\left(M_p, \frac{C_{\text{total}} - w_1 N}{w_p - w_1}\right) \quad (\text{for } p > 1)$$
  *(with $n_{1,\max} = M_1$ as the default boundary if not otherwise bounded).*
