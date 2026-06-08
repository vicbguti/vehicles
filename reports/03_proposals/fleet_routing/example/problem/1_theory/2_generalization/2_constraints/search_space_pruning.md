# Vector Space Behavior and Search Space Pruning

This document details how selection intervals behave in general scenarios, the conditions under which a range of valid subset combinations collapses to a single value, and how this prunes the combination search space.

---

## 1. Candidate Selection Vectors
In a multi-class scenario, the selection of $N$ vehicles is represented by a class-allocation vector:
$$\mathbf{n} = (n_1, n_2, \dots, n_P)$$

A selection vector $\mathbf{n}$ is **admissible** if and only if:
1. All elements lie within their respective selection intervals:
   $$n_p \in [n_{p,\min}, n_{p,\max}] \quad \forall p \in \{1, \dots, P\}$$
2. The elements sum to the target subset size $N$:
   $$\sum_{p=1}^P n_p = N$$

The set of all admissible vectors $\mathcal{V}$ forms a discrete polytope in $\mathbb{Z}^P$.

---

## 2. Range vs. Point Collapse (General vs. Specific Scenario)
Depending on the parameters, the size of the set of admissible vectors $|\mathcal{V}|$ can vary:

### A. General Case (Range of Vectors)
If the candidate pool availability ($M_p$) is abundant and capacities are loose, the intervals $[n_{p,\min}, n_{p,\max}]$ span multiple integers. This results in **multiple valid combination vectors**.

**Example**:
* Let $M_{\text{heavy}} = 10$, $M_{\text{light}} = 20$.
* Fleet capacity $C_{\text{total}} = 12.0$ CUs, target subset size $N = 14$.
* Weights: $w_{\text{heavy}} = 1.0\text{ CU}$, $w_{\text{light}} = \frac{2}{3}\text{ CU}$.
* **Theoretical bounds**: $0 \le n_{\text{heavy}} \le 8$ and $6 \le n_{\text{light}} \le 14$.
* **Admissible vectors**: Any combination $(n_{\text{heavy}}, n_{\text{light}})$ where $n_{\text{heavy}} + n_{\text{light}} = 14$ and they lie in the bounds. Examples:
  * $(0, 14)$ — Total weight: $9.33\text{ CUs}$ (Feasible)
  * $(4, 10)$ — Total weight: $10.67\text{ CUs}$ (Feasible)
  * $(8, 6)$ — Total weight: $12.0\text{ CUs}$ (Feasible)

### B. Point Collapse (Unique Vector)
In highly constrained scenarios, the mathematical bounds meet the physical availability limits in a way that squeezes the intervals until:
$$n_{p,\min} = n_{p,\max}$$
When this occurs, the admissible vector set collapses to a single point ($|\mathcal{V}| = 1$), meaning there is **exactly one** valid combination configuration of vehicle classes. This is what occurred in our concrete 18-vehicle scenario, forcing $n_{\text{SUV}} = 4$ and $n_{\text{Sedan}} = 12$.

---

## 3. Combinatorial Search Space Pruning
The general formula for subset selection:
$$\text{Selection} = \prod_{p=1}^P \binom{M_p}{n_p}$$

By restricting the selection to only admissible vectors $\mathbf{n} \in \mathcal{V}$, the solver can discard all other combinations. 
* **Without Pruning**: A naive solver might evaluate all $\binom{M}{N}$ subsets.
* **With Pruning**: The solver only evaluates $\sum_{\mathbf{n} \in \mathcal{V}} \prod_{p=1}^P \binom{M_p}{n_p}$, drastically reducing the number of candidate subsets that must be sent to the expensive multi-truck partitioning phase.
