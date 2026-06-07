# Solution Visuals

## Overview

This directory contains the **visualisation scripts** used for the vehicle‑registration reporting proposals.

- **class_location/** – Generates the class‑vs‑province heat‑map (`class_location_chart.py`).
- **temporal/** – Generates temporal trend charts (`temporal_trends_combined.py` and the shared plotting helpers in `temporal/core/`).

All scripts read configuration from `config/config.yaml`, produce PNG files under `reports/figures/proposals/…`, and print Spanish success messages.

## Usage
```bash
# Class‑Location matrix (Spanish UI)
python scripts/reporting/proposals/solution_visuals/class_location/class_location_chart.py

# Temporal combined trends (Spanish UI)
python scripts/reporting/proposals/solution_visuals/temporal/temporal_trends_combined.py
```

## Documentation
- Each module has a top‑level docstring describing its purpose.
- Public functions include detailed parameter/return docstrings.
- Inline comments explain non‑obvious logic, such as timeline construction and LogNorm colour scaling.

Feel free to add more docs or screenshots in this README as the visualisations evolve.
