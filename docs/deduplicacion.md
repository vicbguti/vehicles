# Deduplication Workflow Documentation

## Overview
This document records the series of actions performed to clean the vehicle registration dataset, reorganize the raw data, and configure version control to handle large CSV files safely.

## 1. Duplicate Detection & Removal
- A script (`scripts/reporting/audits/quality.py`) was run to identify exact‑row duplicates across all yearly CSVs.
- The duplicate rows (≈ 1.26 M) were removed using `pandas.DataFrame.drop_duplicates()`.
- Each original file was backed up as `<filename>.bak` before being overwritten with the deduplicated version.

## 2. Data Directory Restructuring
- A new directory `data/clean/` was created.
- All **deduplicated** CSV files were moved into `data/clean/` while the original, untouched files (and their `.bak` backups) remain in `data/raw/` for archival purposes.
- This separation makes it clear which files are the source archives and which are the ready‑to‑use datasets.

## 3. Configuration Update
- `config/config.yaml` was updated:
  ```yaml
  data:
    files_pattern: "data/clean/SRI_Vehiculos_Nuevos_*.csv"
  ```
- All reporting and visualisation scripts now reference the cleaned CSV pattern via this config entry, ensuring they operate on the deduplicated data.

## 4. Version‑Control Adjustments
### Git LFS Setup
- Git Large File Storage (LFS) was installed and initialized (`git lfs install`).
- `.gitattributes` was added to track the CSV files with LFS:
  ```text
  data/clean/*.csv filter=lfs diff=lfs merge=lfs -text
  data/raw/*.csv filter=lfs diff=lfs merge=lfs -text
  ```
- The large CSVs are now stored as LFS pointers, avoiding GitHub’s 100 MB file‑size limit.

### Ignoring Backup Files
- `.gitignore` was updated to ignore all `.bak` files and to comment out the previous raw‑CSV ignore rule:
  ```text
  # data/raw/SRI_Vehiculos_Nuevos_*.csv
  *.bak
  ```
- This prevents the backup files from being added to the repository while still keeping them locally for reference.

## 5. Commit History
- The first commit added the deduplication summary, moved the cleaned files, and updated the config.
- A subsequent commit introduced the Git LFS tracking patterns and the `.bak` ignore rule.

## 6. Regenerating Visualisations
After the data layout change, all visualisation scripts were re‑executed to produce up‑to‑date figures based on the cleaned data:
- `class_location_chart.py`
- `temporal_trends_combined.py`
- Other temporal aggregation scripts

These figures now accurately reflect unique vehicle registrations.

---
*Generated on 2026‑06‑07*
