# Mathematical Complexity of the Search Space

To find the absolute optimal packing and routing sequence mathematically, a traditional system must evaluate the combinatorial product of grouping and routing permutations.

## A. Grouping Combinations (Bin Packing)
1. **Selecting the 12 vehicles** (from the 15 available) to fit onto the two trucks:
   $$\binom{15}{12} = \frac{15!}{12! \cdot 3!} = 455 \text{ ways}$$
2. **Splitting the 12 selected vehicles** into Truck 1 (6 vehicles) and Truck 2 (6 vehicles):
   $$\binom{12}{6} = \frac{12!}{6! \cdot 6!} = 924 \text{ ways}$$
* **Total Grouping Configurations**: $455 \times 924 = \mathbf{420,420}$ unique ways to pack the trucks.

## B. Routing Combinations (Traveling Salesperson)
1. **Routing Truck 1** through its 6 stops (excluding the start point):
   $$6! = 720 \text{ route sequences}$$
2. **Routing Truck 2** through its 6 stops:
   $$6! = 720 \text{ route sequences}$$
* **Total Routing Configurations**: $720 \times 720 = \mathbf{518,400}$ unique routes.

## Total Combinations (Grouping $\times$ Routing)
$$\text{Total Search Space} = 420,420 \times 518,400 = \mathbf{217,945,728,000} \text{ (218 Billion Combinations)}$$
