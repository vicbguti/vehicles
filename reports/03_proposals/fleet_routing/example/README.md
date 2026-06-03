# Fleet Routing Examples Index

This directory contains concrete examples, complexity breakdowns, and validation frameworks for the Fleet Routing and Vehicle Distribution system.

## 📂 [Problem Definition](./problem)
This section outlines the constraints, manual baseline methodologies, and mathematical limits of the routing problem:
* [scenario.md](./problem/scenario.md) — The distribution scenario setup (vehicles, capacities, and destinations).
* [status_quo.md](./problem/status_quo.md) — How logistics dispatchers plan routes manually without the system.
* [greedy.md](./problem/greedy.md) — Analysis of why traditional greedy algorithms (nearest-canton first) fail.
* [complexity.md](./problem/complexity.md) — The combinatorial math of the routing search space.
* [intractability.md](./problem/intractability.md) — Mathematical proof showing why scaling the problem parameters makes exact solvers impossible in real-time.
* [formulation.md](./problem/formulation.md) — Generalized algebraic mathematical formulation and cancellation proof of the search space.
* [limits.md](./problem/limits.md) — Comparison of search space times with the world's fastest supercomputers and global compute limits.



## 📂 [Solution Design](./solution)
This section documents the machine learning model, simulator loop, training viability, and runtime expectations:
* [optimized.md](./solution/optimized.md) — The globally optimized approach using Graph Attention Networks.
* [training.md](./solution/training.md) — How the model is trained in our Ecuadorian road simulator.
* [feasibility.md](./solution/feasibility.md) — Why the model training process avoids the curse of combinatorial explosion.
* [training_scale.md](./solution/training_scale.md) — Details on the sample size evaluated during training and the computational budget.
* [validation.md](./solution/validation.md) — Benchmarking mechanics used to ensure performance remains superior to baseline policies.
* [comparisons.md](./solution/comparisons.md) — Concrete scenario outcomes comparing manual vs. optimized solutions.
* [runtime.md](./solution/runtime.md) — Real-time execution and pipeline speed specifications.
