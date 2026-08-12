# Heuristic Failure Modes (Case 1 vs. Case 2)

Although both baseline cases fail to deliver all vehicles (each leaving 6 sedans behind and requiring 3+ rentals), they fail for fundamentally different reasons:

## 1. Case 1 (Sub-Optimal Grouping) — *Coupled Constraints Fail*
* **The Mistake**: The dispatcher groups by location rather than vehicle size class (mixing SUVs and sedans on both trucks).
* **The Consequence**: Because they mix vehicle classes, both trucks run out of physical space/weight quickly. Both trucks end up underutilized (5.01 CUs each), but their remaining capacities (0.99 CU each) are too small to load any of the leftover sedans (2.01 CUs).

---

## 2. Case 2 (Catastrophic Backtracking) — *Routing & Backtracking Fail*
* **The Mistake**: The dispatcher groups all sedans on one truck and all SUVs on the other (which is the correct grouping split). However, they route the sedan truck using a myopic "nearest-canton first" greedy decision (going to Quito first).
* **The Consequence**: While the load split is optimal, the route planning is myopic, forcing a massive **500 km backtrack** to Machala. This wastes 695 km of extra fuel compared to Case 3.
