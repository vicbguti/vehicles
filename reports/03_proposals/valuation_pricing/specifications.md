# Problem 1: Predictive Vehicle Valuation and Pricing

## Appropriate Learning Algorithms
* **XGBoost / LightGBM**: Handles high-cardinality categorical variables (like `Marca` and `Modelo`) and non-linear interactions efficiently.
* **Multi-Layer Perceptron (MLP)**: Deep learning representation matching for complex pricing curves.

## Computational Complexity
High cardinality in categorical features (thousands of distinct vehicle brands and models) requires robust target encoding or entity embeddings to prevent overfitting.
