# Mathematical Intractability of Fleet Routing

To understand why traditional exact solvers fail as the problem scales, consider a setup where we select **20 vehicles** (8 SUVs, 12 Sedans) from **25 available** (10 SUVs, 15 Sedans) to distribute among **3 carrier trucks** (packed as 6, 7, and 7 vehicles) and route them.

## 1. Grouping Combinations (Bin Packing)
* **Selecting the 20 vehicles** (8 SUVs and 12 Sedans) from 25 available:
  $$\text{Selection} = \binom{10}{8} \times \binom{15}{12} = 45 \times 455 = \mathbf{20,475 \text{ ways}}$$

* **Splitting the selected vehicles** among the 3 trucks:
  * Truck 1 carries 2 SUVs and 4 Sedans.
  * Truck 2 carries 3 SUVs and 4 Sedans.
  * Truck 3 carries 3 SUVs and 4 Sedans.
  $$\text{Distribution} = \binom{8}{2, 3, 3} \times \binom{12}{4, 4, 4} = 560 \times 34,650 = \mathbf{19,404,000 \text{ ways}}$$

* **Total Grouping Configurations**: 
  $$20,475 \times 19,404,000 \approx \mathbf{3.97 \times 10^{11}} \text{ configurations}$$

## 2. Routing Combinations (Traveling Salesperson)
* **Truck 1** (6 stops): $6! = 720$ routes
* **Truck 2** (7 stops): $7! = 5,040$ routes
* **Truck 3** (7 stops): $7! = 5,040$ routes
* **Total Routing Configurations**: 
  $$\text{Routing} = 720 \times 5,040 \times 5,040 \approx \mathbf{1.83 \times 10^{10}} \text{ routes}$$

## 3. Total Search Space (Grouping $\times$ Routing)
$$\text{Total Combinations} = 20,475 \times 19,404,000 \times (1.83 \times 10^{10}) \approx \mathbf{7.27 \times 10^{21}} \text{ (7.27 Sextillion Combinations)}$$

---

## Computational Feasibility

If a powerful computer could evaluate **1 million combinations per second**:
* **Time required**: $\approx \mathbf{2.3 \times 10^8 \text{ million years}}$ (over 230 million years).

Even if a supercomputer could evaluate **1 trillion combinations per second**, it would still take over **230 years** to find the absolute optimal solution.

This demonstrates that exact mathematical solvers are **intractable** for real-time operations, highlighting the necessity of heuristic or Deep Reinforcement Learning (DRL) approaches that can evaluate allocations in milliseconds.
