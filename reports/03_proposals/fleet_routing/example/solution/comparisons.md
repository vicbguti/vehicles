# Concrete Examples of the Combinations

Here is a structured comparison of the three outcomes, separating the vehicle grouping, capacity utilization, route sequence, and total costs into distinct columns. Click on each case to see the detailed load calculations and routing paths:

| Case / Scenario | Truck | Grouping (Vehicles) | Capacity Load (CUs) | Route Sequence | Distance (km) | Leftovers | Total Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **[1. Sub-Optimal Grouping](../problem/3_status_quo/status_quo.md)** | Truck 1<br>Truck 2 | 3 Sedans (Quito) + 3 SUVs (Cuenca)<br>3 SUVs (Ambato) + 3 Sedans (Sto. Domingo) | 5.01 / 6.0<br>5.01 / 6.0 | GYE ➔ Cuenca ➔ Quito<br>GYE ➔ Sto. Domingo ➔ Ambato | 635<br>440 | 6 Sedans (Machala, Quito, Sto. Domingo)<br>*(4.02 CUs)* | **1,255 km** driven (fleet)<br>3+ Truck Rentals (third-party) |
| **[2. Catastrophic Backtracking](../problem/2_greedy/greedy.md)** | Truck 1<br>Truck 2 | 6 Sedans (Machala, Quito)<br>6 SUVs (Cuenca, Ambato) | 4.02 / 6.0<br>6.00 / 6.0 | GYE ➔ Quito ➔ Machala<br>GYE ➔ Ambato ➔ Cuenca | 920<br>430 | 6 Sedans (Sto. Domingo, Machala, Quito)<br>*(4.02 CUs)* | **1,640 km** driven (fleet)<br>3+ Truck Rentals (third-party) |
| **[3. Globally Optimized (ML)](./4_optimized/optimized.md)** | Truck 1<br>Truck 2 | 6 SUVs (Cuenca, Ambato)<br>9 Sedans (Machala, Sto. Domingo, Quito) | 6.00 / 6.0<br>6.03 / 6.0 | GYE ➔ Cuenca ➔ Ambato<br>GYE ➔ Machala ➔ Sto. Domingo ➔ Quito | 345<br>600 | 3 Sedans (Machala, Quito, Sto. Domingo)<br>*(2.01 CUs)* | **945 km** driven (fleet)<br>2 Truck Rentals (no third-party) |












