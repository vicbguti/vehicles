# Assuring Model Quality Over Greedy & Status Quo Baselines

To ensure the machine learning model does not fall back to simple greedy heuristics or status quo human planning, the system uses specific training dynamics and evaluation baselines:

## 1. Global Reward Signal (Avoiding the Myopic Trap)
A greedy algorithm makes local, step-by-step decisions (e.g., "always go to the closest town next"). 

The DRL model is trained using a **global reward signal**:
* The agent only receives its reward/penalty *after* the entire routing and packing sequence is complete.
* If the model makes a greedy choice early on that forces an expensive backtrack or requires hiring a 3rd truck later, it receives a major penalty.
* This forces the neural network's weight updates to favor long-term efficiency over immediate, local gains.

## 2. Value Networks (Learned Look-Ahead)
The Pointer Network architecture is supported by a **Value Network** (critic) during training:
* When deciding the next stop or vehicle allocation, the model estimates the *value of all subsequent decisions* that will follow.
* This acts as an automated "look-ahead" mechanism, preventing the model from getting trapped in geographic corners.

## 3. Explicit Baseline Benchmarking
During the validation and testing phases, the model's performance is strictly compared against two automated baselines:
1. **The Greedy Baseline**: A solver that always routes to the nearest neighbor and packs the largest vehicle first.
2. **The Status Quo Baseline**: A programmatic rule-based solver that mimics human dispatchers (grouping purely by geographical zones without balancing multi-truck capacity).

If the trained model's performance drops to or matches these baselines during testing, the training run is flagged as failed. We only deploy models that demonstrate a statistically significant cost reduction (typically 15% to 25% fewer kilometers/trucks) compared to both baselines.

## 4. Constraint Enforcement via Masking
Unlike human dispatchers who might make mistakes under stress (resulting in overloaded trucks or forgotten cargo), the model uses **action masking**:
* At each step, invalid decisions (like routing to a canton that exceeds the truck's weight limit) are mathematically blocked (masked) with $-\infty$ probability.
* This guarantees that the final plan is always 100% feasible and respects physical capacities.
