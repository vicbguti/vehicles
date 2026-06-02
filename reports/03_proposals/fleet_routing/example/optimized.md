# NP-Hard Fleet Logistics & Vehicle Distribution

## What Our Solution Solves (The Optimized Outcome)
Our system looks at the multi-dimensional capacity constraints and geographic graphs simultaneously to find the global optimum:
1. **Optimal Packing (Bin Packing)**: The system calculates that because SUVs take up more space/weight, they should be grouped together on the truck traversing the southern route:
   - *Truck 1* (Sierra Route): Loads the 3 SUVs for Cuenca and the 3 SUVs for Ambato. (Maximizes weight capacity on the specialized mountain-carrier).
   - *Truck 2* (Coast/Northern Route): Loads the 3 sedans for Machala, 3 sedans for Santo Domingo, and 3 sedans for Quito (Total: 9 light sedans, packed efficiently across the flat-bed carrier deck).
2. **Elimination of Wasted Resources**: By calculating the volume configurations, **all 15 vehicles fit onto the 2 trucks**. The company completely eliminates the cost of hiring a 3rd carrier.
3. **Optimal Sequencing**: The system routes Truck 2 in a clean loop: Guayaquil ➔ Machala ➔ Santo Domingo ➔ Quito, avoiding backtracking and minimizing vertical mountain climbs.
