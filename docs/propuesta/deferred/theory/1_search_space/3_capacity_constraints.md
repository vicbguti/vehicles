# Capacity Constraints and Bounds Proof

This document provides the mathematical proof showing why any selected subset of $16$ vehicles must consist of exactly **4 SUVs and 12 Sedans** to fit within the fleet capacity.

---

## 1. Mathematical Formulation of the Bounds
Let a selected subset of size $N = 16$ consist of:
* $S$ = number of SUVs ($0 \le S \le 6$)
* $D$ = number of Sedans ($0 \le D \le 12$)

We have two constraints based on the [Scenario Parameters](./1_scenario_parameters.md):

1. **Size Constraint**: The subset must contain exactly 16 vehicles.
   $$S + D = 16 \implies D = 16 - S$$

2. **Capacity Constraint**: The total capacity unit (CU) sum of the selected vehicles cannot exceed the total fleet capacity ($12.0 \text{ CUs}$).
   $$S(1.0) + D\left(\frac{2}{3}\right) \le 12.0$$

---

## 2. Algebraic Proof
Substituting the size constraint ($D = 16 - S$) into the capacity constraint:

$$S + (16 - S)\frac{2}{3} \le 12$$

Multiply the terms:
$$S + \frac{32}{3} - \frac{2}{3}S \le 12$$

Combine the $S$ terms:
$$\frac{1}{3}S + \frac{32}{3} \le 12$$

Subtract $\frac{32}{3}$ ($10\frac{2}{3}$) from both sides:
$$\frac{1}{3}S \le 12 - \frac{32}{3}$$
$$\frac{1}{3}S \le \frac{36}{3} - \frac{32}{3}$$
$$\frac{1}{3}S \le \frac{4}{3}$$

Multiply by 3:
$$S \le 4$$

---

## 3. Class Bounds Result
* **SUVs ($S$)**: The number of selected SUVs cannot exceed **4** ($S \le 4$).
* **Sedans ($D$)**: Since $D = 16 - S$, we have $D \ge 12$.
* **Candidate Pool Limitation**: We only have 12 Sedans available in total ($D \le 12$).

Therefore, the only mathematically possible composition for a subset of size 16 is:
$$\mathbf{S = 4 \text{ SUVs}} \quad \text{and} \quad \mathbf{D = 12 \text{ Sedans}}$$
