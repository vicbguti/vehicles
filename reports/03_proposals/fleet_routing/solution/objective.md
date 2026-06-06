# NP-Hard Fleet Logistics & Vehicle Distribution: Objective

This document outlines the core optimization objective and targets for the Machine Learning solution.

---

## 1. Objective (The ML Solution)
The core objective is to formulate the vehicle distribution challenge as a **Capacitated Vehicle Routing Problem (CVRP)** and solve it using learning heuristics (detailed in the specifications folder). The system replaces manual dispatching with a neural-network-driven optimization model.

---

## 2. Target Output
The ML model outputs a complete, optimized delivery schedule for each shift:
1. **Route Sequences**: The optimal visiting order of cantons (destinations) for each active carrier truck to minimize total travel distance, geographic backtracking, and fuel consumption.
2. **Vehicle-to-Truck Assignments**: The concrete list of specific vehicles assigned to each carrier truck (verified to be feasible under Capacity Unit constraints).
