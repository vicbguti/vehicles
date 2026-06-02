# Concrete Examples of the Combinations

Here are **three actual examples** of combinations chosen from the 218 billion options, illustrating why random sorting or human heuristics fail:

## Combination 1: Sub-Optimal Grouping & Zigzagging
* **Truck 1**: Loads 3 sedans for Quito + 3 SUVs for Cuenca (Total: 6 vehicles).
  - *Route*: Guayaquil ➔ Cuenca (climb south: 195km) ➔ Quito (climb north: 440km). Total: **635 km**.
* **Truck 2**: Loads 3 SUVs for Ambato + 3 sedans for Santo Domingo (Total: 6 vehicles).
  - *Route*: Guayaquil ➔ Santo Domingo (coast: 290km) ➔ Ambato (climb: 150km). Total: **440 km**.
* **The Leftovers**: 3 sedans for Machala cannot fit. The company must hire a **3rd truck** for Machala (Guayaquil ➔ Machala: 180 km).
* **Total Cost**: **1,255 km driven** and **3 truck rentals paid**.

## Combination 2: Catastrophic Backtracking
* **Truck 1**: Loads 3 sedans for Machala + 3 sedans for Quito (Total: 6 vehicles).
  - *Route*: Guayaquil ➔ Quito (north: 420km) ➔ Machala (backtrack south: 500km). Total: **920 km**.
* **Truck 2**: Loads 3 SUVs for Cuenca + 3 SUVs for Ambato (Total: 6 vehicles).
  - *Route*: Guayaquil ➔ Ambato (280km) ➔ Cuenca (150km). Total: **430 km**.
* **The Leftovers**: 3 sedans for Santo Domingo cannot fit. The company must hire a **3rd truck** for Santo Domingo (Guayaquil ➔ Santo Domingo: 290 km).
* **Total Cost**: **1,640 km driven** and **3 truck rentals paid**.

## Combination 3: The Globally Optimized Solution (ML Output)
* **Truck 1**: Loads 3 SUVs for Cuenca + 3 SUVs for Ambato.
  - *Route*: Guayaquil ➔ Cuenca (195km) ➔ Ambato (150km). Total: **345 km**.
* **Truck 2**: Loads 3 sedans for Machala + 3 sedans for Santo Domingo + 3 sedans for Quito.
  - *Route*: Guayaquil ➔ Machala (180km) ➔ Santo Domingo (320km) ➔ Quito (100km). Total: **600 km**.
* **The Leftovers**: **None**. All 15 vehicles fit perfectly because we grouped the smaller sedans together.
* **Total Cost**: **945 km driven** and **only 2 truck rentals paid**.
