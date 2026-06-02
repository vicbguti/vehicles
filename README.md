# Vehicle Data Analysis & Machine Learning Project

This project focuses on performing an in-depth data quality and quantity analysis of the SRI New Vehicles dataset (2017-2026) and formulating computationally complex learning problems to solve.

## Directory Structure
- `data/`
  - `raw/`: Read-only original files (data dictionary and annual CSV files).
  - `processed/`: Cleaned and merged datasets.
  - `features/`: Extracted features for model training.
- `config/`: Configurations for file paths (`config.yaml`) and declarative schemas (`schemas.yaml`).
- `notebooks/`: Jupyter notebooks separated by analysis focus:
  - `quality/`: Completeness, outliers, and anomalies checking.
  - `quantity/`: Storage, temporal volumes, and category support counts.
  - `problem_formulation.ipynb`: Framing ML problems.
- `src/`: Modular packages:
  - `profiler/`: Core code to profile physical, structural, integrity, and temporal facets.
  - `pipeline/`: Clean, transform (aggregations, scaling, encoding), and validate datasets.
  - `data_dictionary.py`: Parses the Excel Data Dictionary.
  - `features.py` & `models.py`: Feature engineering and ML learning models.
  - `utils.py`: Shared utilities.
- `scripts/`: Operational/CLI runner scripts:
  - `profiling/`: Disk, annual, and cross-period schema evolution profilers.
  - `reporting/`: Summary, quality, volume, and proposals report formatters.
  - `run_pipeline.py`: Master orchestrator script.
- `reports/`: Documented findings:
  - `00_executive_summary.md`
  - `01_quality_audit.md`
  - `02_volume_audit.md`
  - `03_problem_proposals.md`
