# General Mathematical Formulation

This document provides the generalized mathematical proof for the combinatorial search space of the Fleet Routing and Vehicle Distribution problem.

## 1. Parameters
Let the problem variables be defined as:
* $M$ = total available candidate vehicles
* $N$ = number of vehicles to select and deliver ($N \le M$)
* $K$ = number of trucks
* $c_i$ = capacity (number of vehicles) of truck $i$, where the capacities sum to the selected fleet size:
  $$\sum_{i=1}^K c_i = N$$

---

## 2. Component Combinations

### A. Vehicle Selection (Combinations)
The number of ways to select $N$ vehicles from the $M$ available is:
$$\text{Selection} = \binom{M}{N} = \frac{M!}{N!(M-N)!}$$

### B. Fleet Partitioning (Multinomial Distribution)
The selected $N$ vehicles must be distributed onto the $K$ trucks of capacities $c_1, c_2, \dots, c_K$. The number of partition configurations is:
$$\text{Distribution} = \binom{N}{c_1, c_2, \dots, c_K} = \frac{N!}{c_1! \cdot c_2! \cdots c_K!}$$

### C. Route Sequences (Permutations)
For each truck $i$, the number of sequence paths to visit its $c_i$ destinations is $c_i!$. The total route sequences across all $K$ trucks is:
$$\text{Routing} = \prod_{i=1}^K c_i! = c_1! \cdot c_2! \cdots c_K!$$

---

## 3. The Cancellation Proof
The total search space is the product of selection, distribution, and routing:

$$\text{Total Combinations} = \text{Selection} \times \text{Distribution} \times \text{Routing}$$

$$\text{Total Combinations} = \left[ \frac{M!}{N!(M-N)!} \right] \times \left[ \frac{N!}{c_1! \cdot c_2! \cdots c_K!} \right] \times \left[ c_1! \cdot c_2! \cdots c_K! \right]$$

Because the truck routing permutations $c_1! \cdot c_2! \cdots c_K!$ cancel out the truck assignment denominators, and the selected fleet size factorials $N!$ cancel out:

$$\text{Total Combinations} = \frac{M!}{(M-N)!} = P(M, N)$$

---

## 4. Conclusion
Regardless of how truck capacities ($c_i$) or fleet splits ($K$) are configured, the total mathematical search space is always exactly the permutation formula:
$$\mathcal{O}\left( \frac{M!}{(M-N)!} \right)$$
Because this complexity is dominated by a factorial-class growth ($\mathcal{O}(M!)$), any scaling of the candidate size $M$ results in an astronomical search space explosion, proving the mathematical intractability of exact search solvers.
