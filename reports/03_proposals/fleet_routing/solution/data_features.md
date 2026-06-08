# Model Input Features & Metadata Filtering

This document details the specific variables used as inputs (features) for the machine learning model and identifies the metadata fields that are filtered out to prevent training noise.

---

## 1. Input Features (Ingested Data)
The solver ingests the following variables from the historical registration datasets:

* **Demands**: The total counts of vehicles needed per canton, grouped by size classes (`Clase`, `Sub Clase`, `Tipo`) and aggregated weekly to form scenario episodes.
* **Origins**: Latitude and longitude coordinates of ports (e.g., Guayaquil, Manta) or assembly centers (e.g., Quito, Ambato).
* **Destinations**: Latitude and longitude coordinates of the target cantons, mapped from the canton catalog using the canton ID.
* **Vehicle Dimensions (CUs)**: Size class estimations normalized into **Capacity Units (CUs)** (e.g., $1.0\text{ CU}$ for SUVs, $\frac{2}{3}\text{ CU}$ for Sedans) to represent physical space constraints.
* **Carrier Capacity (CUs)**: The maximum loading limit of each truck in the fleet, represented in normalized **Capacity Units (CUs)** (e.g., $6.0\text{ CUs}$ per carrier).

---

## 2. Filtered/Discarded Metadata
To ensure the neural network focuses purely on geography, capacity limits, and route geometry, the following administrative and commercial fields are filtered out during pre-processing:

* **Transaction Details**: `TIPO TRANSACCIÓN` (local vs. imported purchase).
* **Commercial Identifiers**: `MARCA` (Brand/Make), `MODELO` (Model description), `PAIS` (Country of manufacture), `AÑO MODELO` (Model year).
* **Technical Specifications**: `CILINDRAJE` (Engine CC), `TIPO COMBUSTIBLE` (Fuel type).
* **Aesthetics**: `COLOR 1`, `COLOR 2`.
* **Financial Data**: `AVALUO` (Appraisal tax value).
* **Buyer Demographics**: `PERSONA NATURAL - JURIDICA` (Entity type), `TIPO SERVICIO` (Private vs. commercial service).

