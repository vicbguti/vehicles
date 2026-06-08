# Vehicle Data Analysis & Machine Learning Project

This project focuses on performing an in-depth data quality and quantity analysis of the SRI New Vehicles dataset (2017-2026) and formulating computationally complex learning problems to solve.

## Codebase Documentation
A detailed breakdown of the project layout, configurations, source code modules, scripts, and analytical outputs is documented in the:
* **[Project Documentation Index](./docs/README.md)**

---

## Data Source
The raw data is sourced from the official **Servicio de Rentas Internas (SRI) de Ecuador** open data portal:
* **Source URL**: [SRI Ecuador Datasets](https://www.sri.gob.ec/datasets)
* **Dataset Name**: Matriculación Vehicular (Vehículos Nuevos)

---

## How to Run

Before running the operational CLI scripts, ensure you activate the project's virtual environment to load the required dependencies (such as `pyyaml`, `matplotlib`, and `pandas`):

1. **Activate the Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Run the Complete Pipeline**:
   ```bash
   python3 scripts/run_pipeline.py
   ```
   *(Or run individual phases: `python3 scripts/run_profiling.py` or `python3 scripts/run_reporting.py`).*


