# Solution Design Index

This directory documents the machine learning model, simulator training loop, validation metrics, and runtime execution of the optimized routing solution.

## 📋 Evaluation & Comparisons
* [comparisons.md](./comparisons.md) — Concrete comparison matrix linking all three cases (Status Quo, Greedy, and Optimized).

## 📂 Sub-Directories

### [4. Globally Optimized Output](./4_optimized)
* [optimized.md](./4_optimized/optimized.md) — Case 3: The globally optimized approach using Graph Attention Networks.
* [routing_proof.md](./4_optimized/routing_proof.md) — Mathematical proof showing why the routing paths in Case 3 are optimal.

### [System Implementation & Training](./system)
* [why_dl_model.md](./system/why_dl_model.md) — Why a dedicated DL model is required instead of an LLM assistant.
* [training.md](./system/training.md) — How the model is trained in our Ecuadorian road simulator.
* [feasibility.md](./system/feasibility.md) — Why the model training process avoids the curse of combinatorial explosion.
* [training_scale.md](./system/training_scale.md) — Details on sample size evaluated during training and computational budget.
* [validation.md](./system/validation.md) — Benchmarking mechanics used to ensure performance remains superior to baseline policies.
* [runtime.md](./system/runtime.md) — Real-time execution and pipeline speed specifications.

