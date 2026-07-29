# Data

## Source

SRI New Vehicles registrations (`data/clean/SRI_Vehiculos_Nuevos_*.csv`), 2017–2026. One row ≈ one vehicle registration.

## Training episode

An **episode** is a set of vehicles with `(canton, class → CU)` for one time window. **Definition not finalized** — see [06_feasibility.md](./06_feasibility.md) for measured options on SRI data.

Candidates:

| Definition | Description |
|------------|-------------|
| National week | All registrations in ISO week *w* — always large (see feasibility report) |
| Canton-week | Registrations in canton *c*, week *w* — often N ≤ 20 |
| Subsample | Draw N vehicles from a real week (stratified) |

### Columns used (2018+ files)

| Field | CSV column | Model use |
|-------|------------|-----------|
| `CANTÓN` | Canton ID | Destination feature |
| `CLASE` / `SUB CLASE` / `TIPO` | Map to **CU** weight |
| `FECHA PROCESO (DD/MM/AA)` | ISO year-week episode boundary |

2017 is excluded (month-only schema, no process date). 2018–2019 use `FECHA PROCESO (MM/DD/AA)`; 2020+ use `(DD/MM/AA)`.

## Feature mapping example

Raw record (abbreviated):

```csv
…;CLASE;SUB CLASE;TIPO;…;FECHA PROCESO;…;CANTON;…
…;CAMION;PLATAFORMA-C;PESADO;…;28/2/2026;…;10901;…
```

| Raw field | Mapped feature |
|-----------|----------------|
| `CANTON` | Canton ID (optional: lat/lon from catalog) |
| `CLASE` / `SUB CLASE` / `TIPO` | CU value (e.g. SUV 1.0, Sedan 0.67) |
| `FECHA PROCESO` | Week grouping for episode ID |

## Discarded columns

Filtered to reduce noise — not used for loading assignment:

`TIPO TRANSACCIÓN`, `MARCA`, `MODELO`, `PAIS`, `AÑO MODELO`, `CILINDRAJE`, `TIPO COMBUSTIBLE`, `COLOR 1/2`, `AVALUO`, `PERSONA NATURAL - JURIDICA`, `TIPO SERVICIO`, row IDs.

## Subsampling large weeks

If a week has N > 20 vehicles:

* **Do not** invent a fake manifest.
* **Subsample** from that week (stratified by canton/class) so the labeler stays tractable.
* Record parent week ID for traceability.

**Reproducible analysis:** [06_feasibility.md](./06_feasibility.md) (regenerate with `python3 scripts/loading/episode_feasibility.py`).

## Train / validation split

**Temporal split** by `FECHA PROCESO`:

* Train: 2017–2024  
* Validate: 2025–2026  

No random row shuffle across years (avoids leakage).

## Exploratory charts

Pre-computed visuals supporting demand understanding:

* [solution/visuals/spatial/class_distribution.md](./solution/visuals/spatial/class_distribution.md)
* [solution/visuals/spatial/geographic_demands.md](./solution/visuals/spatial/geographic_demands.md)
* [solution/visuals/temporal/](./solution/visuals/temporal/) — seasonality and trends
