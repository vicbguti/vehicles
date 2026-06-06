# NP-Hard Fleet Logistics & Vehicle Distribution

## How We Train Our Solution (The Study Phase)
The machine learning router is not trained on real roads. It learns inside a simulator using our **10-year historical SRI dataset**:
1. **Simulator Setup**: We build a simulator of Ecuador's road network using canton coordinates from the Canton Catalog (`Catálogo_Cantones`).
2. **Realistic Scenarios**: We feed the historical SRI dataset (4.3 million records) into the simulator. The simulator replays real historical sales weeks from 2017 to 2026 so the model faces the actual vehicle mixes and regional demand fluctuations of the Ecuadorian market.
3. **The Learning Loop**: A Reinforcement Learning agent (Pointer Network) tries millions of routing combinations in the simulator:
   - When the agent groups heavy trucks randomly, the simulator gives it a **penalty** for overloading.
   - When the agent leaves trucks half-empty and uses more carriers than necessary, the simulator gives it a **penalty** for poor capacity utilization (or a **reward** for packing trucks close to 100% maximum capacity, minimizing total trucks rented).
   - When the agent routes a truck up and down the Andes unnecessarily, the simulator gives it a **penalty** for wasted fuel.
   - Over millions of iterations, the agent adjusts its neural network weights to maximize its efficiency rewards.
