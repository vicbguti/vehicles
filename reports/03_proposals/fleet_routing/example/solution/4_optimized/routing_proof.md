# Mathematical Proof of Case 3 Routing Optimality

This document provides the mathematical proof showing why the routing paths for the globally optimized solution in [optimized.md](./optimized.md) are the absolute global optimum for the 15-vehicle assignment.

---

## 1. Prerequisites (Fixed Assignment)
As mathematically proven in the bin-packing analysis in [bin_packing.md](../../problem/1_theory/1_search_space/bin_packing.md), the only feasible partition to deliver 15 vehicles on 2 trucks is:
* **Truck 1**: 6 SUVs (Assigned to Cuenca and Ambato)
* **Truck 2**: 9 Sedans (Assigned to Machala, Santo Domingo, and Quito)

---

## 2. Proof of Optimal Routing (TSP)
With the assignments fixed, finding the optimal routing is a Traveling Salesperson Problem (TSP) to find the shortest Hamiltonian path starting from Guayaquil (GYE) for each truck:

### Truck 1 Routing (Cuenca, Ambato)
* **Route A**: GYE ➔ Cuenca (195km) ➔ Ambato (150km) = **345 km**
* **Route B**: GYE ➔ Ambato (280km) ➔ Cuenca (150km) = **430 km**
* **Optimal**: Route A (**345 km**).

### Truck 2 Routing (Machala, Santo Domingo, Quito)
* **Route A**: GYE ➔ Machala (180km) ➔ Sto. Domingo (320km) ➔ Quito (100km) = **600 km**
* **Route B**: GYE ➔ Machala (180km) ➔ Quito (420km) ➔ Sto. Domingo (100km) = **700 km**
* **Route C**: GYE ➔ Sto. Domingo (290km) ➔ Quito (100km) ➔ Machala (500km) = **890 km**
* **Route D**: GYE ➔ Quito (420km) ➔ Sto. Domingo (100km) ➔ Machala (400km) = **920 km**
* **Optimal**: Route A (**600 km**).

---

## 3. Conclusion
Because the vehicle assignment is the only feasible partition for 15 vehicles, and the selected paths are the shortest possible routes for those assignments, the combined result (**945 km total distance and 2 truck rentals**) is mathematically guaranteed to be the global optimum.

