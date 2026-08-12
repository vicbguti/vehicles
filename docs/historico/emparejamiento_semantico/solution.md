# Fuzzy Semantic Entity Resolution (Deduplication)

## Objective (The ML Solution)
Frame this as a metric learning task where the model learns to project raw, inconsistent data-entry strings into a low-dimensional vector space where matching entities lie close to each other.

## Inputs & Targets
* **Inputs**: Pairs of raw, messy vehicle description strings (e.g., `Marca`, `Modelo`, `Sub Clase` inputs).
* **Target**: Similarity score/binary label indicating if the two strings refer to the exact same physical vehicle configuration.
