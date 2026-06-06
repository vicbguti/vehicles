# Source Code Layout

This document describes the structure of the modular source code and packages.

---

## Directory: `src/`

The source directory holds reusable Python modules and packages imports:

* **`profiler/`**:
  * **Purpose**: Core data profiling engine.
  * **Modules**: Computes data completeness, column uniqueness, value evolution/schema drift, and disk storage metrics.
* **`pipeline/`**:
  * **Purpose**: Data cleaning, transformation, and ingestion engine.
  * **Modules**: Cleans raw text, handles duplicates, imputes missing values, and builds merged datasets.
* **`data_dictionary.py`**:
  * **Purpose**: Parser for mapping codes (colors, canton IDs) from the Excel Data Dictionary catalog.
* **`features.py`**:
  * **Purpose**: Feature engineering routines to scale coordinates and aggregate canton-level weekly vehicle demands.
* **`models.py`**:
  * **Purpose**: Machine learning model architectures (like Pointer Networks, Graph Attention Networks) and training loop code.
* **`utils.py`**:
  * **Purpose**: Shared utilities for loading yaml configs, handling logging, and setting up directories.
