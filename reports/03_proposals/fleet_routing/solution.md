# NP-Hard Fleet Logistics & Vehicle Distribution

## Objective (The ML Solution)
Formulate the distribution as a Capacitated Vehicle Routing Problem (CVRP) and solve it using learning heuristics.

## Inputs & Targets
* **Inputs (Features)**:
  * **Demands**: Sum of vehicle volumes registered per canton (`Codigo Canton`), grouped by vehicle size classes (`Clase`, `Sub Clase`).
  * **Origins**: Latitude/longitude coordinates of ports (e.g., Guayaquil, Manta) or assembly centers (e.g., Quito, Ambato).
  * **Destinations**: Latitude/longitude coordinates of cantons (mapped from the canton catalog).
  * **Vehicle Dimensions**: Size class estimations to determine load configurations on carriers.
  * **Carrier Capacity**: Maximum payload weight and volume capacity constraints for each carrier truck in the fleet.
* **Target**: The optimal sequences of delivery routes (visiting order of cantons for each carrier truck) and the corresponding vehicle-to-truck loading configurations that minimize total travel cost while satisfying all capacity constraints.
