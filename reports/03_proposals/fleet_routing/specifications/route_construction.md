# Pointer Network & Sequential Route Construction

This document details the machine learning mechanics used to construct routing sequences dynamically and step-by-step.

---

## 1. The Dynamic Input Challenge (Dynamic Runs)
In traditional sequence-to-sequence neural networks, the output vocabulary (e.g. words in a translation dictionary) is fixed. In fleet logistics, however:
* The set of target canton destinations changes constantly between different executions (runs).
* On Monday, the model may need to route 5 cantons; on Tuesday, it may need to route 12 completely different cantons.

A standard output layer cannot handle variable sequence sizes. A **Pointer Network** solves this by using attention weights as pointers. Instead of choosing from a fixed dictionary, the network's output dictionary is defined dynamically by the inputs fed into it for that specific run.

---

## 2. Autoregressive Route Construction
The route is constructed sequentially (segment-by-segment) in an autoregressive decoder loop:

```
[Start Port] ➔ [Canton A] ➔ [Canton B] ➔ [Canton C] ➔ [Start Port]
   (Step 1)      (Step 2)      (Step 3)      (Step 4)      (Step 5)
```

### Step-by-Step Segment Building:
1. **First Segment (Step 1)**:
   * The model begins at the start coordinates (e.g., GYE port).
   * It calculates attention scores over all input destinations and outputs a probability distribution.
   * The model selects the highest-probability destination (e.g., Canton A).
   * **Result**: First segment is built (`GYE ➔ Canton A`).

2. **Subsequent Segments (Steps 2 to $N$)**:
   * The model's current location is updated to the previously selected canton (Canton A).
   * To prevent the truck from visiting the same canton twice, **action masking** is applied: the attention score for Canton A is set to $-\infty$ (0% probability).
   * The network outputs a probability distribution over the *remaining* unvisited cantons.
   * The model selects the next destination (Canton B).
   * **Result**: Second segment is built (`Canton A ➔ Canton B`).

3. **Return to Origin (Final Step)**:
   * This loop continues until all assigned cantons are visited, at which point the final segment returns the truck to the starting port (`Canton C ➔ GYE`).
