# Training Scale & Compute Budget

To put the efficiency of the Reinforcement Learning approach into perspective:

## 1. Fraction of Search Space Evaluated
Instead of checking sextillions of options (e.g., $1.29 \times 10^{23}$ combinations), the agent only needs to experience **100,000 to 1,000,000 training episodes** in the simulator to converge on near-optimal policies. 
* This means the model evaluates less than **$10^{-15}\%$** of the total possible search space during its entire training lifetime.

## 2. Training Time & Hardware
* The entire learning process takes between **2 to 4 hours** to train on a single standard modern GPU (such as an NVIDIA RTX 3080 or T4).
* The simulator runs training episodes in parallel at thousands of steps per second.

## 3. Runtime Overhead
* Once trained, the resulting neural network model is small (a few megabytes).
* The search overhead at runtime is completely eliminated. Generating a complete route and packing sequence requires only a single forward pass (**inference**) taking **$<10$ms** on standard CPU/GPU hardware.
