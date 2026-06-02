# Executive Summary: Vehicle Data Feasibility Report

This summary profiles the SRI New Vehicles dataset (spanning 2017–2026) to determine the viability of implementing machine learning and deep learning models.

## Dataset Profile At a Glance
* **Official Source**: [SRI Ecuador Datasets Portal](https://www.sri.gob.ec/datasets)
* **Temporal Coverage**: 2017 to 2026 (10 years of annual files)
* **Total Volume**: 4,306,526 vehicle registration records
* **Total Storage on Disk**: 677.99 MB
* **Integrity Status**: **[YELLOW]** - Structurally consistent but shows duplicate records and missing values in specific fields.

## Structural and Schema Consistency
* **Column Uniformity**: Schema comparison indicates that the CSV columns are **consistent** across all years, allowing for robust multi-year concatenation without alignment gaps.
* **Geographic & Categorical Integrity**: Canton and color codes map cleanly to the Data Dictionary catalogs.

## High-Level Modeling Feasibility
* **Volume Viability**: Yes. With over 4,306,526 records, the dataset has ample size for complex deep learning and tree-based structures.
* **Data Quality Viability**: Yes, with cleaning. Deduplication and handling of missing categorical descriptors are required before feeding data into learning algorithms.
