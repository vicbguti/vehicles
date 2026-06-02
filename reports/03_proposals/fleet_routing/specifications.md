# NP-Hard Fleet Logistics & Vehicle Distribution

## Appropriate Learning Algorithms
* **Deep Reinforcement Learning (DRL) with Pointer Networks**: Learns to construct near-optimal routes sequentially by outputting a probability distribution over the remaining candidate cantons.
* **Graph Attention Networks (GATs) / Graph Neural Networks (GNNs)**: Captures spatial-geographic relationships and distance graphs between Ecuadorian cantons.

## Computational Complexity
As the number of destinations and vehicle types scales, the combinations grow exponentially. Exact solvers (like integer programming) become intractable in real-time. Deep Reinforcement Learning agents can evaluate route allocations in **milliseconds** by replacing traditional branch-and-bound searches with learned policy heuristics.
