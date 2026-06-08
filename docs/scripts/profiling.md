# Profiling Sub-System Scripts (`scripts/profiling/`)

These scripts parse raw SRI CSV datasets to build intermediate caches under `reports/cache/`:

* **`disk.py`**: Analyzes file sizes and profiles physical disk footprints.
* **`annual.py`**: Validates annual schema data types, cardinality, and completeness.
* **`evolution.py`**: Inspects temporal drift and record volume evolution.
