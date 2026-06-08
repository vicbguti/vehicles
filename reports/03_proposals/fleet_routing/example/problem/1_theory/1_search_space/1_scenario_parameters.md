# Scenario Parameters

This document defines the common parameters, vehicle properties, and capacity constraints for the 18-vehicle fleet routing scenario. These values serve as the mathematical foundation for the search space, capacity bounds, and complexity calculations.

---

## 1. Carrier Fleet Properties
We have two identical carrier trucks responsible for transporting the vehicles:
* **Number of Trucks ($T$)**: $2$
* **Capacity per Truck ($C$)**: $6.0 \text{ Capacity Units (CUs)}$
* **Total Fleet Capacity ($C_{\text{total}}$)**: $2 \times 6.0 = \mathbf{12.0 \text{ CUs}}$

---

## 2. Port Candidate Pool ($M = 18$)
There are 18 vehicles waiting at the port to be shipped. These vehicles fall into two classes:

* **SUVs** ($6$ available):
  * Unit Capacity: **$1.0 \text{ CU}$**
  * Maximum potential volume: $6 \times 1.0 = \mathbf{6.0 \text{ CUs}}$
* **Sedans** ($12$ available):
  * Unit Capacity: **$\frac{2}{3} \text{ CU}$**
  * Maximum potential volume: $12 \times \frac{2}{3} = \mathbf{8.0 \text{ CUs}}$

* **Total Pool Volume**: $6.0 + 8.0 = \mathbf{14.0 \text{ CUs}}$
