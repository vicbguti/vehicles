# Vehicle Capacity Constraints & Capacity Units (CUs)

To optimize fleet loading, the physical weight limits and deck space constraints of the carrier trucks are standardized using **Capacity Units (CUs)**.

## 1. Carrier Capacity
* Each carrier truck in the fleet has a maximum load capacity of **6.0 CUs**.
* Exceeding 6.0 CUs on any single truck is physically impossible and results in a severe loading penalty.

## 2. Vehicle Classes
Vehicles consume different amounts of Capacity Units based on their physical dimensions (volume) and weight (payload):

* **SUV (Sport Utility Vehicle)**:
  * **CU Value**: **1.0 CU**
  * **Rationale**: SUVs are longer, wider, and heavier, consuming a full unit of deck space and payload capacity. A truck can load at most **6 SUVs**.

* **Sedan**:
  * **CU Value**: **0.67 CU**
  * **Rationale**: Sedans are smaller, shorter, and lighter. Because they consume less deck space and payload, a truck can load up to **9 Sedans** (since $9 \times 0.67 \approx 6.0$ CUs).
