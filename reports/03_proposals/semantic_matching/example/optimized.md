# Fuzzy Semantic Entity Resolution (Deduplication)

## What Our Solution Solves (The Optimized Outcome)
Our system uses a neural network to convert text into semantic vector coordinates:
1. **Vector Alignment**: The model translates both raw strings into 512-dimensional vector coordinates (embeddings).
2. **Semantic Matching**: Because the model has learned the relationship between abbreviations and full words, it places the vector for `TYT HLX D/C 4X4` in the **exact same neighborhood** as `Toyota Hilux Double Cabin 4WD`.
3. **Immediate Deduplication**: The system runs a simple cosine distance check. Because the distance between the two vectors is close to 0, they are automatically grouped under the same master vehicle ID, requiring zero manual rules or developer overhead.
