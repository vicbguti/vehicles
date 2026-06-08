# Concrete Data Mapping Example

This document demonstrates how a single raw record from the SRI dataset is parsed, showing which fields are mapped to model features and which are discarded.

---

## 1. Raw Input Record
Consider the following raw record from the [SRI_Vehiculos_Nuevos_2026.csv](../../../../data/raw/SRI_Vehiculos_Nuevos_2026.csv) file:

```csv
CATEGORÍA;CÓDIGO DE VEHÍCULO;TIPO TRANSACCIÓN;MARCA;MODELO;PAIS;AÑO MODELO;CLASE;SUB CLASE;TIPO;AVALUO;FECHA PROCESO (DD/MM/AAAA);TIPO SERVICIO;CILINDRAJE;TIPO COMBUSTIBLE;FECHA COMPRA (DD/MM/AAAA);CANTON;COLOR 1;COLOR 2;PERSONA NATURAL - JURIDICA
1062980;10607991;COMPRA LOCAL;FOTON;AUMARK S BJ1088 AC 3.8 2P 4X2 TM DIESEL;CHINA POPULAR;2027;CAMION;PLATAFORMA-C;PESADO;27690,00;28/2/2026;PAR;3760;DIESEL;28/2/2026;10901;PLA;;NATURAL
```

---

## 2. Feature Mapping and Pre-Processing

When this record is ingested by the pipeline, it is mapped to the model inputs as follows:

| Raw CSV Field | Value in Record | Mapped Model Feature | Explanation |
| :--- | :--- | :--- | :--- |
| **`CANTON`** | `10901` | **Destination Coordinates** | Mapped to latitude/longitude (e.g. coordinates for Canton Limón Indanza) using the data catalog. |
| **`CLASE`** /<br>**`SUB CLASE`** /<br>**`TIPO`** | `CAMION` /<br>`PLATAFORMA-C` /<br>`PESADO` | **Capacity Units (CUs)** | Classified as a heavy platform cargo, translating to a fixed space value (e.g. $2.0 \text{ CUs}$) for loading constraints. |
| **`FECHA PROCESO`** | `28/2/2026` | **Scenario Grouping** | Grouped into historical weekly demand scenarios (e.g. Week 9 of 2026) for simulated training. |
| **Record Count** | 1 record | **Canton Demand Quantity** | Added to the total count of heavy-cargo deliveries requested for that canton in that week. |

---

## 3. Discarded Metadata Fields

The remaining columns are filtered out during feature selection:

* **Discarded IDs**: `CATEGORÍA` (`1062980`), `CÓDIGO DE VEHÍCULO` (`10607991`).
* **Discarded Commercials**: `TIPO TRANSACCIÓN` (`COMPRA LOCAL`), `MARCA` (`FOTON`), `MODELO` (`AUMARK S...`), `PAIS` (`CHINA POPULAR`), `AÑO MODELO` (`2027`).
* **Discarded Specs**: `AVALUO` (`27690,00`), `CILINDRAJE` (`3760`), `TIPO COMBUSTIBLE` (`DIESEL`), `COLOR 1` (`PLA`), `COLOR 2` (empty).
* **Discarded Demographics**: `TIPO SERVICIO` (`PAR`), `PERSONA NATURAL - JURIDICA` (`NATURAL`).
