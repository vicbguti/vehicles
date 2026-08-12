# Fuzzy Semantic Entity Resolution (Deduplication)

## How We Train Our Solution (The Study Phase)
We train the neural network to learn these semantic abstractions using our **historical SRI dataset**:
1. **Ground Truth Pairs**: We look at our 10 years of data. Even when model descriptions are typed differently, if they share the same unique `Código Vehículo 1` or link to the same entry in the Data Dictionary catalog, we extract them as a **True Match Pair**.
2. **The Contrastive Training Loop**: We train a Siamese Neural Network (using Sentence-Transformers):
   - We feed the network a matching pair (e.g., `TYT HLX` and `Toyota Hilux`). The model is penalized (contrastive loss) if it places their vectors far apart.
   - We feed the network a non-matching pair (e.g., `TYT HLX` and `Hyundai Tucson`). The model is penalized if it places their vectors close together.
3. **Outcome**: Over thousands of epochs, the model learns the "slang" of Ecuadorian car registration data—automatically mapping abbreviations, typos, and synonyms to their correct coordinate locations.
