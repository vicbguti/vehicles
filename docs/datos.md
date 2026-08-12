# Datos

Tres etapas, de los CSV del SRI a los episodios etiquetados por el maestro
exacto. `data/raw/` y `data/processed/` **no existen**: se documentaban aquí,
pero el pipeline nunca los produjo.

## `data/clean/` — los CSV del SRI

Diez archivos anuales, `SRI_Vehiculos_Nuevos_2017.csv` a `…_2026.csv`, 499 MB.
Ya limpios y deduplicados por `src/pipeline/cleaning/`.

**Van por Git LFS.** Sin `git lfs pull` cada archivo son 133 bytes de texto y el
pipeline procesa basura **sin fallar**. Ver [Git LFS](git_lfs.md).

**2017 se descarta** en el modelado: su CSV no trae la columna `FECHA PROCESO`,
así que no se puede situar en el tiempo. La cobertura real es **2018-2026**.

## `data/features/` — vehículos en alcance

`vehicles_in_scope.parquet` (29 MB). Lo produce
`scripts/build_vehicle_features.py`: filtra a las clases de vehículo con
capacidad definida en `config/vehicle_classes.yaml` y añade los campos derivados
que necesita la construcción de episodios (año y semana ISO, cantón).

## `data/episodes/` — los episodios etiquetados

Lo produce `scripts/build_scenarios.py` (~30 min completo; `--limit` para una
muestra).

| Archivo | Contenido |
|---|---|
| `episodes.parquet` | Un registro por episodio: `episode_id`, `iso_year`, `truck_capacities`, `n_loaded`, `cu_utilized`, `optimal` |
| `episode_vehicles.parquet` | Un registro por vehículo del episodio, con la asignación óptima |

Un **episodio** es un manifiesto: los vehículos matriculados en un cantón
durante una semana ISO, más una flota de camiones de capacidades heterogéneas.
34.839 episodios, 534.680 filas de vehículo.

Las columnas `n_loaded` y `cu_utilized` son la salida del maestro exacto
(`src/loading/labeler.py`): el óptimo verdadero, no una heurística. Son la
etiqueta y también la referencia contra la que se mide cada modelo.

### Conjuntos de extrapolación

`extrap_5_6_same`, `extrap_8_10_same` y `extrap_8_10_constanttotal` son
manifiestos re-etiquetados con flotas mayores que las vistas en entrenamiento
(1-4 camiones). Los produce `scripts/build_extrapolation_set.py` y sirven para
comprobar que el diseño por pares generaliza a cualquier número de camiones.

## Qué está versionado y qué no

`data/clean/` va en Git LFS. `data/features/` y `data/episodes/` están en
`.gitignore`: son derivados reproducibles y regenerarlos es más barato que
versionarlos.
