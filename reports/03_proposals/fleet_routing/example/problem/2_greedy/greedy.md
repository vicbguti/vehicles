# Case 2: Naive Greedy Routing & Backtracking

Traditional greedy heuristics (such as always routing to the nearest canton first) often trap carriers in highly sub-optimal paths:

Here are the configuration details:

| Configuration Metric | Truck 1 Details | Truck 2 Details | Leftovers (Third-Party Carrier) |
| :--- | :--- | :--- | :--- |
| **Grouping (Vehicles)** | 3 sedans (Machala) + 3 sedans (Quito) | 3 SUVs (Cuenca) + 3 SUVs (Ambato) | 6 sedans (4 Sto. Domingo, 1 Machala, 1 Quito) |
| **Capacity Load (CUs)** | 4.02 / 6.0 CUs | 6.0 / 6.0 CUs *(Exactly Full)* | 4.02 CUs *(Cannot fit on Truck 1 or 2)* |
| **Route Path** | GYE ➔ Quito ➔ Machala *(Severe Backtrack)* | GYE ➔ Ambato ➔ Cuenca | GYE ➔ Santo Domingo |
| **Distance (km)** | 920 km | 430 km | 290 km *(Sto. Domingo delivery distance)* |

### Cost & Resource Inefficiency
* **Total Distance**: **1,640 km** driven (fleet trucks only).
* **Truck Rentals**: **3+ rentals paid** (due to poor capacity planning leaving 6 leftover vehicles behind, requiring expensive third-party carrier services).
* **The Backtracking Trap**: Because the dispatcher naively routed Truck 1 to Quito first, the truck was forced to backtrack 500 km all the way to the southern canton of Machala.


