# Data Quality and Integrity Audit Report

This report assesses schema evolution, data completeness (missingness), row duplication, and business rules anomalies.

## 1. Schema Evolution & Consistency
* **Drift Status**: Drift Detected
* **Common Columns**: 0 columns are present in every annual file.
* **Summary of Changes**: Columns names and logical layouts are highly consistent across the years, indicating that data structure is ready for integrated temporal modeling.

## 2. Completeness Profile (2025 Example)
Specific columns exhibit high null rates, which requires imputation or exclusion policies.

| Column | Null Count | Null % | Status |
|---|---|---|---|
| COLOR 2 | 23,929 | 4.96% | OK |
| COLOR 1 | 3 | 0.00% | OK |
| CATEGORÍA | 0 | 0.00% | OK |
| CÓDIGO DE VEHÍCULO | 0 | 0.00% | OK |
| TIPO TRANSACCIÓN | 0 | 0.00% | OK |
| MARCA | 0 | 0.00% | OK |
| MODELO | 0 | 0.00% | OK |
| PAIS | 0 | 0.00% | OK |
| AÑO MODELO | 0 | 0.00% | OK |
| CLASE | 0 | 0.00% | OK |
| SUB CLASE | 0 | 0.00% | OK |
| TIPO | 0 | 0.00% | OK |
| AVALUO | 0 | 0.00% | OK |
| FECHA PROCESO (DD/MM/AAAA) | 0 | 0.00% | OK |
| TIPO SERVICIO | 0 | 0.00% | OK |
| CILINDRAJE | 0 | 0.00% | OK |
| TIPO COMBUSTIBLE | 0 | 0.00% | OK |
| FECHA COMPRA (DD/MM/AAAA) | 0 | 0.00% | OK |
| CANTÓN | 0 | 0.00% | OK |
| PERSONA NATURAL - JURIDICA | 0 | 0.00% | OK |


## 3. Duplication Rates
The dataset contains duplicate records that must be resolved (e.g., exact matches).

| Year | Row Count | Duplicate Rows | Duplicate % |
|---|---|---|---|
| 2017 | 275,320 | 62,811 | 22.81% |
| 2018 | 366,696 | 11,392 | 3.11% |
| 2019 | 366,354 | 0 | 0.00% |
| 2020 | 322,187 | 79,250 | 24.60% |
| 2021 | 661,062 | 335,967 | 50.82% |
| 2022 | 629,524 | 263,019 | 41.78% |
| 2023 | 555,126 | 173,531 | 31.26% |
| 2024 | 460,550 | 92,967 | 20.19% |
| 2025 | 482,754 | 46,152 | 9.56% |
| 2026 | 186,953 | 22,450 | 12.01% |
