# Matrix Representation and Search Construction

This document details how the binary assignment matrix $x$ is structured mathematically and how a solver algorithm constructs it via tree search.

---

## 1. Matrix Structure and Dimensions
To represent the assignment of $N$ selected vehicles onto $K$ carrier trucks, the assignment variable is represented as a $K \times N$ binary matrix:

$$x \in \{0, 1\}^{K \times N}$$

* **Rows ($i \in \{1, \dots, K\}$)** represent the carrier trucks.
* **Columns ($j \in \{1, \dots, N\}$)** represent the selected cargo vehicles.

### Row and Column Vectors
* Each column vector $\mathbf{x}_{\ast, j}$ represents the assignment profile of vehicle $j$.
* Each row vector $\mathbf{x}_{i, \ast}$ represents the selection of vehicles loaded onto truck $i$.

---

## 2. Constraints in Matrix Operations
The partitioning conditions from [bin_packing.md](./bin_packing.md) can be written using matrix algebra operations:

### A. Unique Assignment (Column Sums)
Every selected vehicle must be assigned to exactly one truck. Therefore, each column sum must equal $1$:
$$\sum_{i=1}^K x_{ij} = 1 \quad \forall j \in \{1, \dots, N\}$$

### B. Capacity Limit (Vector Dot Product)
Let $\mathbf{w} = (w_1, w_2, \dots, w_N)^T$ be the column vector of vehicle weights. The sum of capacity units on truck $i$ is the dot product of the $i$-th row vector with the weight vector, which cannot exceed capacity $C_i$:
$$\mathbf{x}_{i, \ast} \cdot \mathbf{w} \le C_i \quad \forall i \in \{1, \dots, K\}$$

### C. Tight Capacity Equality Condition (No-Slack Proof)
If the total cargo weight matches the total fleet capacity exactly ($\mathbf{1} \cdot \mathbf{w} = \sum_{i=1}^K C_i$), all inequality constraints collapse into exact equalities (no slack capacity is mathematically possible on any truck).

**Proof**:
Summing the capacity constraints across all $K$ trucks:
$$\sum_{i=1}^K (\mathbf{x}_{i, \ast} \cdot \mathbf{w}) \le \sum_{i=1}^K C_i$$

Because each vehicle is uniquely assigned to exactly one truck, we can factor the sum:
$$\sum_{i=1}^K (\mathbf{x}_{i, \ast} \cdot \mathbf{w}) = \left(\sum_{i=1}^K \mathbf{x}_{i, \ast}\right) \cdot \mathbf{w} = \mathbf{1} \cdot \mathbf{w}$$

Given that the total weight matches the fleet capacity ($\mathbf{1} \cdot \mathbf{w} = \sum C_i$), we have:
$$\sum_{i=1}^K (\mathbf{x}_{i, \ast} \cdot \mathbf{w}) = \sum_{i=1}^K C_i$$

For the sum of constraints to equal the sum of capacities when each individual constraint is $\mathbf{x}_{i, \ast} \cdot \mathbf{w} \le C_i$, there cannot be any slack on any truck. Therefore, we must satisfy the exact equality:
$$\mathbf{x}_{i, \ast} \cdot \mathbf{w} = C_i \quad \forall i \in \{1, \dots, K\}$$

---

## 3. Algorithmic Matrix Construction (Search Tree)
A solver builds this matrix by assigning vehicles to trucks column-by-column.

### A. Decision Tree Structure
The search space forms a $K$-ary decision tree of depth $N$:
* **Root (Depth 0)**: Empty matrix (all $x_{ij} = 0$).
* **Depth $j$**: The $j$-th column $\mathbf{x}_{\ast, j}$ is populated by setting exactly one row entry $x_{ij} = 1$ (assigning vehicle $j$ to truck $i$).
* **Leaves (Depth $N$)**: A fully populated assignment matrix.

```
                  [ Root ] (Empty Matrix)
                 /   |    \
          Row 1     ...    Row K      <-- Decision for Vehicle 1 (Col 1)
         /  |  \          /  |  \
       R1  ...  RK      R1  ...  RK   <-- Decision for Vehicle 2 (Col 2)
```

### B. Backtracking and Pruning
The solver traverses the tree using depth-first search (DFS) with backtracking:
1. **Incremental Validation**: At depth $j$, after assigning vehicle $j$ to truck $i$, the solver checks if the capacity constraint for truck $i$ is still satisfied:
   $$\sum_{m=1}^j w_m x_{im} \le C_i$$
2. **Pruning**: If the capacity limit is exceeded, the constraint is violated. The solver **prunes** the entire branch below this node, backtracks to the parent decision, and tries the next truck row.
