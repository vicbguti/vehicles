# Partition Feasibility for N = 16

This document details the mathematical constraints and proof showing why there are exactly three valid ways to partition the selected 16 vehicles (4 SUVs and 12 Sedans) between two carrier trucks.

---

## 1. Capacity Equations
To deliver the 16 selected vehicles, they must be partitioned into the two $6.0\text{ CU}$ trucks. Let:
* $X$ = number of SUVs on Truck 1 (where $0 \le X \le 4$)
* $Y$ = number of Sedans on Truck 1 (where $0 \le Y \le 12$)

Truck 2 must carry the remaining $(4 - X)$ SUVs and $(12 - Y)$ Sedans. The capacity constraints are:

* **Truck 1**: $X + \frac{2}{3}Y \le 6.0 \implies 3X + 2Y \le 18$
* **Truck 2**: $(4 - X) + \frac{2}{3}(12 - Y) \le 6.0 \implies 3(4 - X) + 2(12 - Y) \le 18 \implies 3X + 2Y \ge 18$

Because both inequalities must be satisfied simultaneously, there is no slack capacity and we must satisfy the exact equality:
$$3X + 2Y = 18$$

---

## 2. Exhaustive Search for Integer Solutions
Because vehicles cannot be divided, $X$ and $Y$ must be integers. We evaluate all possible integer values for $X \in \{0, 1, 2, 3, 4\}$ to solve for $Y = \frac{18 - 3X}{2}$:

* **$X = 0$**:
  $$Y = \frac{18 - 0}{2} = 9 \quad (\mathbf{\text{Valid Integer Solution}})$$
* **$X = 1$**:
  $$Y = \frac{18 - 3}{2} = 7.5 \quad (\text{Invalid Fractional Solution})$$
* **$X = 2$**:
  $$Y = \frac{18 - 6}{2} = 6 \quad (\mathbf{\text{Valid Integer Solution}})$$
* **$X = 3$**:
  $$Y = \frac{18 - 9}{2} = 4.5 \quad (\text{Invalid Fractional Solution})$$
* **$X = 4$**:
  $$Y = \frac{18 - 12}{2} = 3 \quad (\mathbf{\text{Valid Integer Solution}})$$

---

## 3. Valid Partition Configurations
The exhaustive search proves that only three partition configurations are mathematically possible:

| Configuration | Truck 1 Load | Truck 2 Load | Truck 1 CUs | Truck 2 CUs |
| :--- | :--- | :--- | :--- | :--- |
| **Balanced** | 2 SUVs + 6 Sedans | 2 SUVs + 6 Sedans | $2(1.0) + 6(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) | $2(1.0) + 6(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) |
| **Asymmetric A** | 0 SUVs + 9 Sedans | 4 SUVs + 3 Sedans | $9(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) | $4(1.0) + 3(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) |
| **Asymmetric B** | 4 SUVs + 3 Sedans | 0 SUVs + 9 Sedans | $4(1.0) + 3(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) | $9(\frac{2}{3}) = \mathbf{6.0 \text{ CUs}}$ (100%) |

