# Method

## Problem formulation

**Capacitated fleet loading** — assign each vehicle to Truck 1, Truck 2, or **Defer**, subject to 6.0 CU per truck.

Formal constraints: [deferred/theory/2_generalization/3_partitioning/bin_packing.md](./deferred/theory/2_generalization/3_partitioning/bin_packing.md).

---

## 1. Label generation (teacher)

**Exhaustive search** on episodes with N ≤ ~20:

1. Enumerate feasible assignments.
2. Score: maximize vehicles loaded → CU utilization → minimize leftovers.
3. Store best assignment as **label** per vehicle.

* Scenarios from real SRI weeks ([03_data.md](./03_data.md)).
* Labels are **automatic**, not hand-annotated.
* Solver is our code — not a black-box library.

---

## 2. Trainable model (student)

**Supervised imitation** in **PyTorch** (we implement architecture, loss, and training loop).

| Component | Choice |
|-----------|--------|
| Input | Variable-size set of vehicles (canton + class/CU) |
| Architecture | Per-vehicle classifier or attention over vehicles |
| Output | Truck A / Truck B / Defer |
| Loss | Cross-entropy vs teacher labels |
| Inference | **Capacity masking** — block assignments that exceed 6.0 CU |

Architecture must handle **variable N** (same weights for 12 or 40 vehicles).

---

## 3. Baselines

Implemented by us for comparison ([05_evaluation.md](./05_evaluation.md)):

* **Status quo** — regional proximity grouping ([example/problem/3_status_quo/status_quo.md](./example/problem/3_status_quo/status_quo.md))
* **Greedy** — first-fit / canton-order ([example/problem/2_greedy/greedy.md](./example/problem/2_greedy/greedy.md)); evaluate **grouping only**, not route km

---

## 4. Why learning (not just the teacher)

| Setting | Role of model |
|---------|----------------|
| Small N, same as training | Approximate teacher; mainly demonstrates learning |
| Large N at inference | Fast feasible assignment where exhaustive times out |
| Held-out SRI weeks | Generalize without re-running search |

See [02_scope.md](./02_scope.md) for honest limits on optimality claims.

---

## Planned modules

| Module | Role |
|--------|------|
| `src/loading/scenarios.py` | Weekly manifests from CSVs |
| `src/loading/labeler.py` | Exhaustive teacher |
| `src/loading/assigner.py` | PyTorch model |
| `scripts/train_loading.py` | Training |
| `scripts/eval_loading.py` | Metrics vs baselines |
