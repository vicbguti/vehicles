# NP-Hard Fleet Logistics & Vehicle Distribution

## What They Do WITHOUT Our Solution (The Status Quo)
Without our machine learning system, the dispatcher relies on **human intuition** and **Google Maps**:
1. **Manual Allocation (Intuition)**: The dispatcher groups deliveries by proximity:
   - *Truck 1* gets loaded with the 3 sedans for Quito and the 3 SUVs for Ambato (Total: 6 vehicles).
   - *Truck 2* gets loaded with the 3 SUVs for Cuenca and the 3 sedans for Santo Domingo (Total: 6 vehicles).
   - *The Leftovers*: The 3 sedans for Machala do not fit. The distributor has to hire an expensive third-party carrier to deliver the remaining 3 cars.
2. **Point-to-Point Routing (Google Maps)**: The dispatcher inputs the stops into Google Maps to find the road paths. Google Maps tells them the travel times, but cannot check if the truck is overloaded or advise on how to swap cars between trucks to eliminate the need for the third carrier.
3. **The Result**: High cost. The company had to pay for a 3rd carrier truck and spent hours manually planning.
