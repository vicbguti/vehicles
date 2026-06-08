# Fuzzy Semantic Entity Resolution (Deduplication)

## What They Do WITHOUT Our Solution (The Status Quo)
Without our machine learning system, database engineers rely on **manual rules (Regex)** and **fuzzy string matchers**:
1. **Rule-Based Pipelines**: Developers write thousands of nested replacement rules:
   - `if Model contains 'HLX' then Model = 'HILUX'`
   - `if Model contains 'D/C' then Model = 'DOBLE CABINA'`
   - *Limitation*: This is extremely **brittle**. If a new dealership enters the system and types `HILX` or `DBL CAB`, the rules fail to match, and the record falls through. An engineer has to continually write new code.
2. **String Distance Metrics (Levenshtein Distance)**: The system calculates how many character edits it takes to turn one string into another.
   - *Limitation*: The Levenshtein distance between `TYT HLX D/C 4X4 2.7` and `Toyota Hilux Double Cabin 4x4 Active` is very high because they share few letters in the same positions. The algorithm flags them as unrelated.
3. **The Result**: High cost. The company employs developers to constantly patch regex files, and many records remain unmatched, leading to inaccurate statistics.
