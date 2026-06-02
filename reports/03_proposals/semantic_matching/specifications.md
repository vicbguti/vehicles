# Fuzzy Semantic Entity Resolution (Deduplication)

## Appropriate Learning Algorithms
* **Sentence-Transformers (Bi-encoders)**: Encodes vehicle text inputs into dense vectors to calculate cosine similarities.
* **Siamese Neural Networks with Contrastive Loss**: Trains the model to minimize distances for true matches and maximize distances for non-matches.

## Computational Complexity
This is a cognitive task that is trivial for humans using common sense (e.g. knowing "TYT" means "Toyota") but very difficult for traditional algorithms due to low character-level similarities. Deep embeddings allow the machine to learn semantic abstractions of abbreviations and synonyms, bypassing manual regex-based rule-matching.
