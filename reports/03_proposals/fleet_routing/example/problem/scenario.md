# NP-Hard Fleet Logistics & Vehicle Distribution

## The Concrete Scenario (The Daily Task)
Every Monday morning, a major Ecuadorian vehicle distributor at the Port of Guayaquil receives a shipment of **18 newly imported vehicles** that must be delivered to regional dealerships across **5 cantons**:
* **Destinations & Available Quantities**: 
  - Quito (4 sedans)
  - Ambato (3 SUVs)
  - Cuenca (3 SUVs)
  - Santo Domingo (4 sedans)
  - Machala (4 sedans)
* **The Constraints**: The distributor has **two carrier trucks**, each with a maximum capacity of **6.0 Capacity Units (CUs)**. Detail on vehicle class values can be found in [constraints.md](./constraints.md). Because of capacity limits, the fleet can carry at most **15 vehicles** (6 SUVs and 9 sedans) in a single run.
* **The Goal**: Select **15 vehicles** from the 18 available and assign them to the 2 trucks under capacity constraints. Route sequencing is outside the current loading-only scope.



