# Data Quantity and Volume Audit Report

This report analyzes the physical size, memory footprint, record counts, and temporal volume distribution of the vehicle dataset.

## 1. Physical Storage Footprint
The dataset comprises 10 files, totaling **677.99 MB** on disk.

| File Name | Size (MB) | Loaded Rows |
|---|---|---|
| SRI_Vehiculos_Nuevos_2017.csv | 39.08 MB | 275,320 |
| SRI_Vehiculos_Nuevos_2018.csv | 58.22 MB | 366,696 |
| SRI_Vehiculos_Nuevos_2019.csv | 61.42 MB | 366,354 |
| SRI_Vehiculos_Nuevos_2020.csv | 47.91 MB | 322,187 |
| SRI_Vehiculos_Nuevos_2021.csv | 107.09 MB | 661,062 |
| SRI_Vehiculos_Nuevos_2022.csv | 100.60 MB | 629,524 |
| SRI_Vehiculos_Nuevos_2023.csv | 86.89 MB | 555,126 |
| SRI_Vehiculos_Nuevos_2024.csv | 72.14 MB | 460,550 |
| SRI_Vehiculos_Nuevos_2025.csv | 75.02 MB | 482,754 |
| SRI_Vehiculos_Nuevos_2026.csv | 29.62 MB | 186,953 |


## 2. Temporal Volume & Growth Trends
Annual registration counts show the historical demand progression.

| Period | Record Count | YoY Growth (Abs) | YoY Growth (%) |
|---|---|---|---|
| 2017 | 275,320 | - | - |
| 2018 | 366,696 | +91376 | 33.19% |
| 2019 | 366,354 | -342 | -0.09% |
| 2020 | 322,187 | -44167 | -12.06% |
| 2021 | 661,062 | +338875 | 105.18% |
| 2022 | 629,524 | -31538 | -4.77% |
| 2023 | 555,126 | -74398 | -11.82% |
| 2024 | 460,550 | -94576 | -17.04% |
| 2025 | 482,754 | +22204 | 4.82% |
| 2026 | 186,953 | -295801 | -61.27% |


## 3. Memory Profile & Optimization Suggestions
When loaded into memory as raw DataFrames, the average annual memory footprint is significant.
Converting categorical fields (such as `Marca`, `Modelo`, `País`, and `Clase`) to the pandas `category` type will reduce the deep memory consumption by **50% to 75%** on average.
