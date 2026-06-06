# Case 3: Globally Optimized Solution (ML Output)

Our machine learning model solves the Capacitated Vehicle Routing Problem (CVRP) by optimizing packing constraints and geographic route graphs simultaneously:

Here are the configuration details:

| Configuration Metric | Truck 1 Details | Truck 2 Details | Leftovers (Unselected) |
| :--- | :--- | :--- | :--- |
| **Grouping (Vehicles)** | 9 sedans (3 Machala, 3 Santo Domingo, 3 Quito) | 4 SUVs (2 Cuenca, 2 Ambato) + 3 sedans (1 Machala, 1 Santo Domingo, 1 Quito) | 2 SUVs (1 Cuenca, 1 Ambato) |
| **Capacity Load (CUs)** | 6.0 / 6.0 CUs *(100% Utilized)* | 6.0 / 6.0 CUs *(100% Utilized)* | 2.0 CUs *(To be delivered in next shift)* |
| **Route Path** | GYE ➔ Machala ➔ Santo Domingo ➔ Quito | GYE ➔ Cuenca ➔ Ambato (plus local sedan drop-offs) | None |
| **Distance (km)** | 600 km | 345 km | 0 km |

### Cost & Resource Optimization
* **Total Distance**: **945 km** driven (fleet trucks only).
* **Truck Rentals**: **2 rentals paid** (no third-party rentals needed, as the 2 leftovers are scheduled for the next shift rather than requiring an extra truck).
* **Optimized Solution**: Grouping the lighter/smaller sedans on Truck 1 allows the truck to carry 9 vehicles while staying within its capacity limits. Truck 2 carries the remaining 4 SUVs and 3 sedans, bringing both trucks to exactly 100% capacity utilization.
