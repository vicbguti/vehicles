# Machine Learning & Computational Problem Proposals

Based on the variables present in the vehicle database, we propose three computationally complex problems that can be solved using learning algorithms.

---

### Problem 1: Predictive Vehicle Valuation and Pricing
* **Objective**: Predict the appraised value (`Valor Avaluo`) of a vehicle based on its technical specifications.
* **Inputs (Features)**: `Cilindraje`, `Año Modelo`, `Marca`, `Modelo`, `País`, `Clase`, `Sub Clase`.
* **Target**: `Valor Avaluo` (Continuous numeric value).
* **Appropriate Algorithms**:
  * **XGBoost / LightGBM**: Handles high-cardinality categorical variables (like `Marca` and `Modelo`) and non-linear interactions efficiently.
  * **Multi-Layer Perceptron (MLP)**: Deep learning representation matching for complex pricing curves.
* **Complexity**: High cardinality in categoricals (thousands of distinct vehicle models) requires robust target encoding or entity embeddings.

---

### Problem 2: Regional Market Demand Forecasting
* **Objective**: Forecast the volume of new vehicle registrations by province and canton for future months.
* **Inputs**: Historical monthly counts grouped by `Codigo Canton`, `Marca`, and `Clase`.
* **Target**: Sum of vehicle registrations (Volume).
* **Appropriate Algorithms**:
  * **LSTM / GRU Recurrent Neural Networks**: Captures monthly seasonality and temporal sequence dependencies.
  * **Prophet / SARIMAX**: Statistical time-series forecasting for localized regions.
* **Complexity**: Modeling fine-grained time-series (hundreds of cantons and brands) is computationally intensive and suffers from sparsity in small cantons.

---

### Problem 3: Vehicle Type & Classification Clustering (Unsupervised Representation)
* **Objective**: Group vehicle models into semantic clusters based on engine size, valuation, country of origin, and subclass to identify market segments.
* **Inputs**: Combined numeric and encoded categorical features.
* **Appropriate Algorithms**:
  * **K-Means / HDBSCAN**: Identifies natural groupings and outliers.
  * **Autoencoders**: Learns low-dimensional representations for complex multi-attribute mappings.
* **Complexity**: Requires mixing numeric values with high-dimensional encoded categorical attributes without distorting distance metrics.
