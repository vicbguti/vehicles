# NP-Hard Fleet Logistics & Vehicle Distribution

## How We Use Our Solution (The Runtime Phase)
Once trained, the model runs as a lightweight software brain. On Monday morning:
1. **Input**: The logistics manager uploads the day's manifest (the 15 vehicles and their destination cantons) into the application.
2. **Inference**: The manifest is passed through the trained neural network. In **less than 10 milliseconds** (a single forward pass), the model outputs the complete plan:
   - Which vehicles to load on Truck 1 and Truck 2.
   - The exact loading layout.
   - The optimal turn-by-turn stop sequence.
3. **Disruption Handling**: If a landslide blocks the Aloag-Santo Domingo highway at 10:00 AM, the driver logs the delay. The system runs another 10ms check and instantly re-routes the fleet around the blockage.
