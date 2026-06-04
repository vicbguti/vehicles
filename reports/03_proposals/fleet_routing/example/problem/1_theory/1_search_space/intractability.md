# Mathematical Intractability of Fleet Routing

To understand why traditional exact solvers fail as the problem scales, consider a setup where we select **20 vehicles** from **25 available** to distribute among **3 trucks** (packed as 6, 7, and 7 vehicles) and route them.

## 1. Grouping Combinations (Bin Packing)
* **Selecting 20 vehicles from 25 available**:
  $$\binom{25}{20} = 53,130 \text{ ways}$$
* **Splitting the 20 selected vehicles** among the 3 trucks (6, 7, and 7):
  $$\binom{20}{6} \times \binom{14}{7} \times \binom{7}{7} = 38,760 \times 3,432 \times 1 = 133,024,320 \text{ ways}$$
* **Total Grouping Configurations**: 
  $$53,130 \times 133,024,320 \approx \mathbf{7.07 \times 10^{12}} \text{ configurations}$$

## 2. Routing Combinations (Traveling Salesperson)
* **Truck 1** (6 stops): $6! = 720$ routes
* **Truck 2** (7 stops): $7! = 5,040$ routes
* **Truck 3** (7 stops): $7! = 5,040$ routes
* **Total Routing Configurations**: 
  $$720 \times 5,040 \times 5,040 \approx \mathbf{1.83 \times 10^{10}} \text{ routes}$$

## 3. Total Search Space (Grouping $\times$ Routing)
$$\text{Total Combinations} \approx (7.07 \times 10^{12}) \times (1.83 \times 10^{10}) \approx \mathbf{1.29 \times 10^{23}} \text{ (129 Sextillion Combinations)}$$

---

## Computational Feasibility

If a powerful computer could evaluate **1 million combinations per second**:
* **Time required**: $\approx \mathbf{4.1 \times 10^{15} \text{ years}}$ (over 4 quadrillion years).

Even if a supercomputer could evaluate **1 trillion combinations per second**, it would still take over **4,100 years** to find the absolute optimal solution.

This demonstrates that exact mathematical solvers are **intractable** for real-time operations, highlighting the necessity of heuristic or Deep Reinforcement Learning (DRL) approaches that can evaluate allocations in milliseconds.
