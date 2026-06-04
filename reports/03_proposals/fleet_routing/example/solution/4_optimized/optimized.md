# Case 3: Globally Optimized Solution (ML Output)

Our machine learning model solves the Capacitated Vehicle Routing Problem (CVRP) by optimizing packing constraints and geographic route graphs simultaneously:

Here are the configuration details:

| Configuration Metric | Truck 1 Details | Truck 2 Details | Leftovers (Unselected) |
| :--- | :--- | :--- | :--- |
| **Grouping (Vehicles)** | 3 SUVs (Cuenca) + 3 SUVs (Ambato) | 3 sedans (Machala) + 3 sedans (Santo Domingo) + 3 sedans (Quito) | 3 sedans (1 Machala, 1 Quito, 1 Sto. Domingo) |
| **Capacity Load (CUs)** | 6.0 / 6.0 CUs *(100% Utilized)* | 6.03 / 6.0 CUs *(Optimal threshold fit)* | 2.01 CUs *(To be delivered in next shift)* |
| **Route Path** | GYE ➔ Cuenca ➔ Ambato | GYE ➔ Machala ➔ Santo Domingo ➔ Quito | None |
| **Distance (km)** | 345 km | 600 km | 0 km |

### Cost & Resource Optimization
* **Total Distance**: **945 km** driven (fleet trucks only).
* **Truck Rentals**: **2 rentals paid** (no third-party rentals needed, as the 3 leftovers are scheduled for the next shift rather than requiring an extra truck).
* **Balanced Solution**: Grouping the lighter/smaller sedans on Truck 2 allows the truck to carry 9 vehicles while staying within its capacity limits. Truck 1 is reserved exclusively for the heavier, bulkier SUVs.


