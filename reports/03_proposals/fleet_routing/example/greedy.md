# Why Greedy Heuristics Fail

Traditional greedy algorithms (e.g., always routing to the nearest canton first, or packing the largest vehicle first) are highly suboptimal for fleet routing due to:

## 1. The Backtracking Trap
Local, myopic choices made early in a route often force the carrier into a geographic corner. To deliver the remaining vehicles, the truck is forced to make a long, fuel-wasting backtracking journey.

## 2. Coupled Constraints
Grouping (Bin Packing) and routing (Traveling Salesperson) cannot be solved independently:
* A greedily packed truck might maximize deck space but require a highly inefficient delivery sequence across distant cantons (e.g., grouping vehicles for Quito and Cuenca on the same truck).
* A route planned purely for geographical proximity will frequently violate physical truck capacity constraints, leaving vehicles stranded.

## 3. Learned Greedy (ML Alternative)
Deep Reinforcement Learning agents construct routes sequentially, retaining the millisecond execution speed of greedy algorithms. However, their step-by-step decisions are guided by a value network trained on global optimization outcomes rather than immediate local gains.
