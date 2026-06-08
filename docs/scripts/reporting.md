# Reporting & Visuals Scripts (`scripts/reporting/`)

These scripts build final Markdown reports and compile visualization figures:

## Sub-Runners
* **`run_audits.py`**: Orchestrates data quality audit builders.
* **`run_proposals.py`**: Orchestrates machine learning proposal builders.

## Audit Builders (`scripts/reporting/audits/`)
* **`summary.py`**: Compiles the Executive Summary report.
* **`quality.py`**: Compiles the data quality report.
* **`visuals.py`**: Renders YoY registration trends charts.
* **`volume/`**: Houses sub-scripts for disk storage, growth, and memory reports.

## Proposal Visuals (`scripts/reporting/proposals/`)
* **`solution_visuals/`**:
  * `class_distribution.py`: Charts class distribution counts.
  * `geographic_demands.py`: Plots coordinate demand bubble-maps.
