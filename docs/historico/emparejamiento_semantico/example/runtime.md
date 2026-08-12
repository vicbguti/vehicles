# Fuzzy Semantic Entity Resolution (Deduplication)

## How We Use Our Solution (The Runtime Phase)
Once trained, the model runs as a fast lookup engine:
1. **Ingestion**: When new daily registration CSV files are uploaded, each row's description string is passed through the neural network.
2. **Vector Lookup**: The system converts the new string into its vector representation and queries a fast vector database (like FAISS or Milvus).
3. **Deduplication**: The database instantly returns the closest matching master vehicle catalog entry in milliseconds. Even if a brand new typo is introduced, the model maps it correctly based on spelling similarities, requiring zero developer intervention.
