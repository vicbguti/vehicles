# Concrete Examples of the Combinations

Here is a structured comparison of the three outcomes, separating the vehicle grouping, capacity utilization, route sequence (illustrative only), and total costs into distinct columns. Click on each case to see the detailed load calculations and routing paths:

> Route sequence and distances are shown for context only. The project evaluation focuses on grouping, CU load, and leftovers.

| Case / Scenario | Truck | Grouping (Vehicles) | Capacity Load (CUs) | Route Sequence | Distance (km) | Leftovers | Total Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **[1. Sub-Optimal Grouping](../problem/3_status_quo/status_quo.md)** | Truck 1<br>Truck 2 | 3 Sedans (Quito) + 3 SUVs (Cuenca)<br>3 SUVs (Ambato) + 3 Sedans (Sto. Domingo) | 5.0 / 6.0 CUs<br>5.0 / 6.0 CUs | GYE ➔ Cuenca ➔ Quito<br>GYE ➔ Sto. Domingo ➔ Ambato | 635<br>440 | 6 Sedans (Machala, Quito, Sto. Domingo)<br>*(4.0 CUs)* | **1,255 km** driven (fleet)<br>3+ Truck Rentals (third-party) |
| **[2. Catastrophic Backtracking](../problem/2_greedy/greedy.md)** | Truck 1<br>Truck 2 | 3 Sedans (Machala) + 3 Sedans (Quito)<br>3 SUVs (Cuenca) + 3 SUVs (Ambato) | 4.0 / 6.0 CUs<br>6.0 / 6.0 CUs | GYE ➔ Quito ➔ Machala<br>GYE ➔ Ambato ➔ Cuenca | 920<br>430 | 6 Sedans (Sto. Domingo, Machala, Quito)<br>*(4.0 CUs)* | **1,640 km** driven (fleet)<br>3+ Truck Rentals (third-party) |
| **[3. Globally Optimized (ML)](./4_optimized/optimized.md)** | Truck 1<br>Truck 2 | 9 Sedans (Machala, Sto. Domingo, Quito)<br>4 SUVs (Cuenca, Ambato) + 3 Sedans | 6.0 / 6.0 CUs<br>6.0 / 6.0 CUs | GYE ➔ Machala ➔ Sto. Domingo ➔ Quito<br>GYE ➔ Cuenca ➔ Ambato | 600<br>345 | 2 SUVs (Cuenca, Ambato)<br>*(2.0 CUs)* | **945 km** driven (fleet)<br>2 Truck Rentals (no third-party) |
