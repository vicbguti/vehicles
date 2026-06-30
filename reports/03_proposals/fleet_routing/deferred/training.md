# NP-Hard Fleet Logistics & Vehicle Distribution

## How We Train Our Solution (The Study Phase)

The model is trained via **supervised imitation learning** — no RL, no simulator loop.

### 1. Teacher: exhaustive search (labeler)
For training episodes with **N ≤ ~20 vehicles**:
1. Enumerate all feasible truck-A / truck-B / defer assignments.
2. Score each assignment: maximize vehicles loaded → CU utilization → minimize deferred.
3. Store the best assignment as the **label** for each vehicle.

Scenarios are built from real SRI weeks ([04_method.md](../04_method.md)).

### 2. Student: trainable classifier
The student is a PyTorch model that predicts Truck A / Truck B / Defer:

| Component | Choice |
|-----------|--------|
| Input | Variable-size set of vehicles (canton + class/CU) |
| Architecture | Per-vehicle classifier or attention over vehicles |
| Output | Truck A / Truck B / Defer |
| Loss | Cross-entropy vs teacher labels |
| Inference | **Capacity masking** — block assignments exceeding 6.0 CU |

The architecture handles **variable N** (same weights for 12 or 40 vehicles).

### 3. Why this approach
- **Small N** — the student approximates the teacher; demonstrates learning.
- **Large N at inference** — produces fast feasible assignments where exhaustive search times out.
- **Held-out weeks** — generalizes to unseen SRI periods without re-running search.
