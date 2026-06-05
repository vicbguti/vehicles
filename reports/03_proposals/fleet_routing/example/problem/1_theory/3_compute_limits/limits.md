# Physical Limits of Routing Computation

To put the scale of the fleet routing problem into perspective, we can compare the combinatorial search space against the world's most powerful computers.

## 1. Comparison to the World's Fastest Supercomputer (Frontier)
The world's fastest supercomputer, **Frontier** (located at Oak Ridge National Laboratory), has a peak computational capacity of approximately **1.2 Exaflops** ($1.2 \times 10^{18}$ floating-point operations per second).

* **Evaluation Overhead**: To check a single routing and packing combination (calculating distances, checking truck capacity constraints, and comparing results), a computer must execute at least **1,000 floating-point operations (FLOPs)**.
* **Supercomputer Speed**: Working at 100% capacity, Frontier can process roughly **$1.2 \times 10^{15}$ combinations per second**.
* Time Required: Finding the absolute mathematically optimal route for just **20 vehicles and 3 trucks** (using brute-force search) on the entire supercomputer would take:
  $$\frac{7.27 \times 10^{21}}{1.2 \times 10^{15} \text{ combinations/sec}} \approx 6,058,333 \text{ seconds} \approx \mathbf{70.1 \text{ days}}$$

---

## 2. Scaling Beyond a Single Supercomputer
If we scale the problem parameters slightly further to **25 vehicles and 4 trucks** (selecting 25 out of 30 available), the combinations grow to approximately **$2 \times 10^{30}$**.

* **Global Compute Power**: If we combined the power of **every computer, server, and smartphone on Earth** (an estimated global capacity of $\approx 10^{21}$ operations per second):
* **Time Required**: It would take **over 60,000 years** of continuous global computation to find the absolute optimum.

---

## 3. Conclusion
Brute-force exact search is not just inconvenient; it quickly becomes physically impossible. This mathematical reality proves that logistics routing cannot rely on traditional exact solvers for real-time operations, necessitating heuristic or Deep Reinforcement Learning (DRL) models that can output near-optimal schedules in milliseconds.
