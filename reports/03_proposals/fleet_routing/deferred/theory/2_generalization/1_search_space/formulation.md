# General Mathematical Formulation (Multi-Class)

This document provides the generalized mathematical proof for the combinatorial search space of the Fleet Routing and Vehicle Distribution problem, accounts for multiple vehicle classes, and shows how capacity constraints affect the cancellation proof.

---

## 1. Parameters
Let the problem variables be defined as:
* $P$ = number of vehicle classes (e.g., SUVs, Sedans).
* $M_p$ = set of available candidate vehicles of class $p \in \{1, \dots, P\}$, where the total candidate pool size is:
  $$M = \sum_{p=1}^P M_p$$
* $n_p$ = number of selected vehicles of class $p$ to deliver, where the total selected cargo size is:
  $$N = \sum_{p=1}^P n_p$$
* $K$ = number of carrier trucks.
* $c_{ip}$ = capacity (number of vehicles) of class $p$ assigned to truck $i$.
* $c_i$ = total vehicle count on truck $i$ (sum of all classes):
  $$c_i = \sum_{p=1}^P c_{ip}$$
  *(Note that $\sum_{i=1}^K c_i = N$ and $\sum_{i=1}^K c_{ip} = n_p$).*

---

## 2. Component Combinations

### A. Vehicle Selection (Combinations)
Because candidate vehicles are selected from their respective class pools, the total number of selection configurations is the product of combinations for each class:
$$\text{Selection} = \prod_{p=1}^P \binom{M_p}{n_p} = \prod_{p=1}^P \frac{M_p!}{n_p!(M_p-n_p)!}$$

### B. Fleet Distribution (Multinomial Splits)
For each class $p$, the $n_p$ selected vehicles must be split among the $K$ trucks. The number of ways to distribute class $p$ is given by the multinomial coefficient. The total distribution combinations is the product over all classes:
$$\text{Distribution} = \prod_{p=1}^P \binom{n_p}{c_{1p}, c_{2p}, \dots, c_{Kp}} = \prod_{p=1}^P \frac{n_p!}{\prod_{i=1}^K c_{ip}!}$$

### C. Route Sequences (Permutations)
Each truck $i$ must route the total $c_i$ vehicles assigned to it. Since routing orders the vehicles regardless of class, the routing sequences for truck $i$ is $c_i!$:
$$\text{Routing} = \prod_{i=1}^K c_i! = \prod_{i=1}^K \left( \sum_{p=1}^P c_{ip} \right)!$$

---

## 3. The Multi-Class Cancellation Proof
The total search space is the product of selection, distribution, and routing:

$$\text{Total Combinations} = \text{Selection} \times \text{Distribution} \times \text{Routing}$$

$$\text{Total Combinations} = \left[ \prod_{p=1}^P \frac{M_p!}{n_p!(M_p-n_p)!} \right] \times \left[ \prod_{p=1}^P \frac{n_p!}{\prod_{i=1}^K c_{ip}!} \right] \times \left[ \prod_{i=1}^K c_i! \right]$$

The chosen class count factorials ($n_p!$) cancel out between the selection denominator and the distribution numerator:

$$\text{Total Combinations} = \left( \prod_{p=1}^P \frac{M_p!}{(M_p-n_p)!} \right) \times \prod_{i=1}^K \frac{c_i!}{\prod_{p=1}^P c_{ip}!}$$

---

## 4. Complexity Classification
The total search space consists of two parts:
1. **Permutations per Class**: $\prod_{p=1}^P P(M_p, n_p)$ which represents the unique sequences of vehicle IDs chosen within each class.
2. **Interleaving Factor**: $\prod_{i=1}^K \frac{c_i!}{\prod_{p=1}^P c_{ip}!}$ which represents the number of ways to mix/interleave the classes on each truck's route.

### Comparison to Homogeneous Scenario ($P = 1$)
If there is only a single homogeneous vehicle class, then $c_{i1} = c_i$. The interleaving factor collapses to $1$ because $\frac{c_i!}{c_i!} = 1$, and the formula simplifies back to:
$$\text{Total Combinations} = P(M, N)$$

With multiple classes, the search space grows by the class interleaving factor, adding to the combinatorial explosion. This confirms that multi-class capacity limits increase both packing constraints and the final permutation search space.
