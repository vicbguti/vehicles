# Fuzzy Semantic Entity Resolution (Deduplication)

## The Concrete Scenario (The Daily Task)
Every day, a vehicle market research firm consolidates vehicle registration records from hundreds of different dealerships across Ecuador. The raw data contains columns like `Marca` (Brand), `Modelo` (Model), and `Sub Clase`. 
Because operators type these details manually under time pressure, the database receives highly inconsistent representations of the same vehicle:
* **Record 1**: Brand: `TYT`, Model: `HLX D/C 4X4 2.7`
* **Record 2**: Brand: `TOYOTA`, Model: `HILUX DOBLE CABINA 4WD`
* **The Goal**: Automatically identify that both records refer to the exact same physical vehicle configuration (Toyota Hilux Double Cab 4x4) so they can be grouped together for tax valuations and market share reporting.
