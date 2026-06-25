# Why Training is Computationally Feasible

While finding the absolute optimal routing sequence via exact mathematical solvers is intractable (requiring the evaluation of $1.29 \times 10^{23}$ combinations), training a **Deep Reinforcement Learning (DRL)** agent remains completely feasible. 

The training process avoids the combinatorial explosion through three main mechanisms:

## 1. Gradient-Guided Learning vs. Exhaustive Search
A traditional solver must search the entire combinatoric space because it needs to guarantee the absolute global optimum. 

Instead of searching, a DRL agent learns using **Policy Gradients** and **Gradient Descent**:
* The agent starts by taking random routing actions in the simulator.
* The simulator returns a reward or penalty based on the efficiency of the routes.
* The agent calculates the gradient of the expected reward with respect to the neural network weights.
* It updates the weights in the direction of positive gradient, steadily climbing toward high-quality solutions.

This is analogous to finding the peak of a hill in thick fog: by walking in the direction where the ground slopes upward, you can reach the peak without mapping every coordinate of the mountain first.

## 2. Pruning the Search Space Early
A DRL agent does not spend time evaluating obviously terrible options. During the initial steps of the learning loop, the network quickly learns basic geometric and physical constraints:
* Overloading a truck results in immediate, heavy penalties.
* Routing a truck back and forth across distant regions wastes fuel and incurs time penalties.

Once the model learns these constraints, the probability of selecting those actions drops to near-zero. The agent effectively prunes away **99.999%** of the search space, focusing its training iterations only on the remaining, highly promising candidate routes.

## 3. Generalization (Learning Features, Not Route Instances)
A traditional solver starts from scratch for every new daily manifest, solving a new NP-hard instance from the ground up. 

A neural network (such as a Graph Attention Network) learns **general spatial-geographic features** and **logical rules** from the simulator:
* Spatial relationships between cantons.
* Strategic clustering of vehicle weights and dimensions.

Once these general features are learned, the model does not "solve" the problem via search at run-time. It performs **inference** (a single forward pass through the network taking $<10$ms) to construct a high-quality route instantly.
