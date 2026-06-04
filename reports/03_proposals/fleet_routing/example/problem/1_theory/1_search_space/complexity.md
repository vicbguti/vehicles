# Mathematical Complexity of the Search Space

To find the absolute optimal packing and routing sequence mathematically, a traditional system must evaluate the combinatorial product of grouping and routing permutations.

In our scenario, we must select **15 vehicles** (6 SUVs, 9 sedans) from **18 available** (6 SUVs, 12 sedans) and distribute them to the two carrier trucks:

## A. Grouping Combinations (Bin Packing)
1. **Selecting the 15 vehicles** from 18 available:
   $$\binom{18}{15} = \frac{18!}{15! \cdot 3!} = 816 \text{ ways}$$
2. **Splitting the 15 selected vehicles** into Truck 1 (6 SUVs) and Truck 2 (9 sedans):
   $$\binom{15}{6} = \frac{15!}{6! \cdot 9!} = 5,005 \text{ ways}$$
* **Total Grouping Configurations**: $816 \times 5,005 = \mathbf{4,084,080}$ unique ways to pack the trucks.

## B. Routing Combinations (Traveling Salesperson)
1. **Routing Truck 1** through its 6 stops (excluding the start point):
   $$6! = 720 \text{ route sequences}$$
2. **Routing Truck 2** through its 9 stops:
   $$9! = 362,880 \text{ route sequences}$$
* **Total Routing Configurations**: $720 \times 362,880 = \mathbf{261,273,600}$ unique routes.

## Total Combinations (Grouping $\times$ Routing)
$$\text{Total Search Space} = 4,084,080 \times 261,273,600 = \mathbf{1,067,041,833,984,000} \text{ (1.07 Quadrillion Combinations)}$$

