# Configuration Layout

This document describes the structure and usage of the project configurations.

---

## Directory: `config/`

The config folder contains yaml files that control paths, file groupings, and schema validation rules across the pipeline:

* **`config.yaml`**:
  * **Purpose**: Defines global execution parameters.
  * **Keys**: Specifies relative and absolute file paths (`raw_dir`, `processed_dir`, `reports_dir`, etc.) used by scripts to locate files.
* **`schemas.yaml`**:
  * **Purpose**: Defines the declarative database schema validation.
  * **Keys**: Specifies expected column names, nullability constraints, and data type specifications (e.g. converting `Cilindraje` to integer, `Avaluo` to float) to validate raw CSV files during profiling.
