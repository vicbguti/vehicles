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

Siete conjuntos, en dos ejes, todos producidos por
`scripts/build_extrapolation_set.py`. Miden qué pasa fuera del sobre de
entrenamiento —1-4 camiones y hasta 20 vehículos— cambiando **una sola variable
por conjunto**. Resultados en
[resultados del MLP §6](modelo/resultados.md#6-generalizacion-fuera-del-sobre-de-entrenamiento).

| Conjunto | Eje | Qué cambia |
|---|---|---|
| `extrap_5_6_same`, `extrap_8_10_same`, `extrap_8_10_constanttotal` | camiones | Mismos manifiestos, flota mayor, reetiquetados por el maestro |
| `extrap_maxn_25`, `_30`, `_40`, `_50` | tamaño de manifiesto | Se reconstruyen desde `data/features/` con un tope mayor de vehículos |

## Qué está versionado y qué no

| Ruta | Cómo | Tamaño |
|---|---|---|
| `data/clean/` | Git LFS | 535 MB |
| `data/episodes/` | **blobs normales** | 11 MB |
| `data/features/` | `.gitignore` | 29 MB |

`data/episodes/` se versiona porque es el **conjunto de ejemplos** con el que se
entrenan y evalúan los seis modelos, y la entrega pide que esté cargado en el
remoto. Estuvo excluido bajo la regla genérica de «no commitear datasets
grandes», que a 11 MB no aplica.

Va como blob normal y **no** por LFS a propósito: el objetivo es que clonar baste
para reproducir el entrenamiento, y mandarlo a LFS reintroduciría el `git lfs
pull` obligatorio. Con los episodios en el clon, ni `data/clean/` ni los ~30 min
de `build_scenarios.py` hacen falta para entrenar. El hook
`check-added-large-files` corta en 1 MB y tiene una excepción acotada a
`data/episodes/*.parquet`; el límite global sigue vigente para todo lo demás, que
es lo que empuja los binarios de modelo hacia LFS.

`data/features/` sigue fuera: es un paso intermedio que sólo hace falta para
**reconstruir** los episodios (o para generar el eje de extrapolación por tamaño
de manifiesto), no para usarlos.
