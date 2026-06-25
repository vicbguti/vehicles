# Mathematical Complexity of the Search Space

To find the absolute optimal packing and routing sequence mathematically, a traditional system must evaluate the combinatorial product of grouping and routing permutations.

In our scenario, we must select **16 vehicles** (4 SUVs, 12 sedans) from **18 available** (6 SUVs, 12 sedans) and distribute them to the two carrier trucks:

## A. Grouping Combinations (Bin Packing)
1. **Selecting the 16 vehicles** (4 SUVs and 12 Sedans) from 18 available:
   $$\binom{6}{4} \times \binom{12}{12} = 15 \times 1 = \mathbf{15 \text{ ways}}$$
   *(Note: Any other selection of 16 vehicles exceeds the total fleet capacity of 12.0 CUs).*

2. **Splitting the 16 selected vehicles** into the two carrier trucks (Truck 1 and Truck 2):
   * **Balanced Partition** (8 vehicles per truck: 2 SUVs + 6 Sedans each):
     $$\binom{4}{2} \times \binom{12}{6} = 6 \times 924 = 5,544 \text{ ways}$$
   * **Asymmetric Partition** (Truck 1 with 9 Sedans; Truck 2 with 4 SUVs + 3 Sedans, or vice versa):
     $$2 \times \left[\binom{4}{0} \times \binom{12}{9}\right] = 2 \times 220 = 440 \text{ ways}$$
   * **Total Valid Splits**: $5,544 + 440 = \mathbf{5,984 \text{ ways}}$

* **Total Grouping Configurations**: $15 \times 5,984 = \mathbf{89,760}$ unique valid ways to pack the trucks.

## B. Routing Combinations (Traveling Salesperson)
Routing complexity depends on the chosen partition configuration:

### Configuration 1: Balanced Partition (8 Stops per Truck)
1. **Routing Truck 1** (8 stops):
   $$8! = 40,320 \text{ route sequences}$$
2. **Routing Truck 2** (8 stops):
   $$8! = 40,320 \text{ route sequences}$$
* **Routing Configurations (Balanced)**: $40,320 \times 40,320 = \mathbf{1,625,702,400}$ unique routes.

### Configuration 2: Asymmetric Partition (9 Stops & 7 Stops)
1. **Routing Truck 1** (9 stops):
   $$9! = 362,880 \text{ route sequences}$$
2. **Routing Truck 2** (7 stops):
   $$7! = 5,040 \text{ route sequences}$$
* **Routing Configurations (Asymmetric)**: $362,880 \times 5,040 = \mathbf{1,828,915,200}$ unique routes.

---

## Total Combinations (Grouping $\times$ Routing)
Depending on the partition scheme chosen, the search space size ranges:
* **For Balanced Partitions**:
  $$15 \times 5,544 \times 1,625,702,400 = \mathbf{135,193,411,584,000} \text{ (135.2 Trillion Combinations)}$$
* **For Asymmetric Partitions**:
  $$15 \times 440 \times 1,828,915,200 = \mathbf{12,070,840,320,000} \text{ (12.07 Trillion Combinations)}$$

## C. Grouping-only timing (no routing)

If we ignore routing and evaluate only the grouping (bin-packing) configurations, the search space is the **89,760** grouping configurations computed above. Example runtimes:

- At **1 million evaluations/second**: $$\frac{89,760}{10^{6}} \approx \mathbf{0.09\ \text{seconds}}.$$\
- At **1 trillion evaluations/second**: $$\frac{89,760}{10^{12}} \approx \mathbf{90\ \text{nanoseconds}}.$$

This demonstrates that for the toy N=16/available=18 case the bin-packing enumeration alone is trivial to exhaust, which matches the discussion in [06_feasibility.md](../../../reports/03_proposals/fleet_routing/06_feasibility.md) about small-N tractability and why routing is the dominant contributor to intractability.
