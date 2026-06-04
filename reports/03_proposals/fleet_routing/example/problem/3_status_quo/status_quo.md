# Case 1: Manual Status Quo Allocation

Without our machine learning system, the dispatcher groups and loads vehicles onto trucks based on rough regional proximity. Here are the configuration details:


| Configuration Metric | Truck 1 Details | Truck 2 Details | Leftovers (Third-Party Carrier) |
| :--- | :--- | :--- | :--- |
| **Grouping (Vehicles)** | 3 sedans (Quito) + 3 SUVs (Cuenca) | 3 SUVs (Ambato) + 3 sedans (Santo Domingo) | 6 sedans (4 Machala, 1 Quito, 1 Sto. Domingo) |
| **Capacity Load (CUs)** | 5.01 / 6.0 CUs | 5.01 / 6.0 CUs | 4.02 CUs *(Cannot fit on Truck 1 or 2)* |
| **Route Path** | GYE ➔ Cuenca ➔ Quito | GYE ➔ Santo Domingo ➔ Ambato | GYE ➔ Machala / Quito / Sto. Domingo |
| **Distance (km)** | 635 km | 440 km | 180 km *(Machala delivery distance)* |

### Cost & Resource Inefficiency
* **Total Distance**: **1,255 km** driven (fleet trucks only).
* **Truck Rentals**: **3+ rentals paid** (due to poor capacity planning leaving 6 leftover vehicles behind, requiring expensive third-party carrier services).
* **Coupled Constraints Fail**: Grouping Quito (North) and Cuenca (South) on the same truck leads to massive geographic zigzagging.


