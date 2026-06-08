# Data Pipeline Directory Layout

This document describes the structure and storage design of the data folder.

---

## Directory: `data/`

The data directory is divided into three stages representing the lifecycle of the dataset from raw ingestion to model features:

* **`raw/`**:
  * **Status**: Read-Only.
  * **Contents**: Original files including the Excel data dictionary and the 10 annual CSV files (`SRI_Vehiculos_Nuevos_2017.csv` through `SRI_Vehiculos_Nuevos_2026.csv`) downloaded from the SRI open portal.
* **`processed/`**:
  * **Status**: Generated.
  * **Contents**: Cleaned, deduplicated, and combined multi-year datasets created by the preprocessing pipeline.
* **`features/`**:
  * **Status**: Generated.
  * **Contents**: Formatted and scaled feature matrices (e.g. canton demands, distance coordinates) ready to be loaded into training models.
