# Fuzzy Semantic Entity Resolution (Deduplication)

## The Real-World Problem
Vehicle model and subclass names are typed manually by operators at different dealerships and registration centers in Ecuador. This creates massive inconsistencies due to typos, varying word orders, and abbreviations:
* **Examples**:
  - `TYT HLX D/C 4WD 2.7` vs. `Toyota Hilux Double Cabin 4x4 Active`
  - `HND CIV EX 1.5` vs. `Honda Civic EX Turbo`
* **Impact**: Standard databases cannot join or aggregate these records, leading to skewed market share reports, duplicate inventory records, and inconsistent tax valuations.


