# Carga de flota — asignación vehículo-camión

Planificación automatizada de la distribución de vehículos en camiones de carga,
a partir del dataset de vehículos nuevos del SRI de Ecuador (2018-2026).

Dado un manifiesto —los vehículos matriculados en un cantón durante una semana—
y una flota de camiones con capacidades heterogéneas, hay que asignar cada
vehículo a un camión o diferirlo, sin exceder ninguna capacidad, maximizando en
este orden estricto: **cuántos vehículos se transportan** y, como desempate,
**cuánto espacio se aprovecha**.

El óptimo exacto lo calcula un buscador propio por programación dinámica
(`src/loading/labeler.py`, sin solvers externos), y ese óptimo es la etiqueta
con la que se entrenan seis modelos por aprendizaje supervisado por imitación:
un MLP en Keras, XGBoost, LightGBM, un transformer en PyTorch, un Random Forest
y una regresión logística multinomial.

## Puesta en marcha

Requiere [uv](https://docs.astral.sh/uv/) y Git LFS. **Python 3.12 es
obligatorio**: TensorFlow 2.21 no publica ruedas para versiones posteriores.

```bash
uv sync
git lfs install --local && git lfs pull
```

**Para entrenar y evaluar los modelos, LFS no hace falta.** El conjunto de
ejemplos —`data/episodes/`, 11 MB— viene versionado en el clon, así que
`train_mlp.py`, `train_classical.py` y el pipeline Kedro funcionan de inmediato.
`scripts/build_scenarios.py` sólo se ejecuta para **reconstruir** los episodios
desde cero (~30 min), y sólo eso necesita los CSV.

El paso de LFS sí es obligatorio para el resto: perfilado, reportes y
reconstrucción de datos derivados. Los diez CSV de `data/clean/` (535 MB) se
almacenan como punteros; sin descargarlos, esas etapas leen 133 bytes de texto
por archivo y producen resultados sin sentido **sin fallar**. Para comprobarlo:

```bash
head -c 40 data/clean/SRI_Vehiculos_Nuevos_2025.csv   # no debe decir "version https://git-lfs..."
```

Con [`just`](https://github.com/casey/just) instalado, `just setup` hace todo lo
anterior y además activa los hooks de pre-commit.

## Servicio de distribución (API)

Los seis modelos del repositorio se sirven como API FastAPI en `src/api/`:
los cuatro *pairwise* (XGBoost, LightGBM, el transformer y el MLP de Keras) sin
límite de camiones ni de capacidad, y los dos de ancho fijo (Random Forest y
regresión logística) con el tope `max_trucks` de su artefacto aplicado
explícitamente por el servicio:

```bash
FLEET_LOADING_MODEL=mlp fleet_loading/.venv/bin/python \
    -m uvicorn src.api.main:app --port 8000
```

`FLEET_LOADING_MODEL` elige el modelo al arrancar (`xgboost` | `lightgbm` |
`attention` | `mlp` | `rf` | `logreg`; por defecto `xgboost`) y
`GET /api/health` confirma cuál quedó activo. El MLP requiere Keras (usa el
backend de torch si no hay TensorFlow). Endpoints: `POST /api/manifest`
(valida el CSV y la flota) y
`POST /api/distribute` (genera el plan, y devuelve con qué modelo y en cuántos
milisegundos). Detalle en [`docs/api.md`](./docs/api.md).

## Uso

```bash
# MLP  (data/episodes/ ya viene en el clon: nada que construir antes)
uv run python scripts/train_mlp.py
uv run python scripts/evaluate_mlp.py

# Random Forest y regresión logística
uv run python scripts/train_classical.py --model rf --split time
uv run python scripts/train_classical.py --model rf \
    --refit-from artifacts/rf/training_report.json   # reajusta sin repetir Optuna

# XGBoost, LightGBM y transformer (pipeline Kedro)
uv sync --extra gbt --extra attention --extra kedro
cd fleet_loading && uv run --project .. kedro run    # o: just train-fleet

# Reconstruir los datos derivados desde los CSV (requiere git lfs pull)
uv run python scripts/build_vehicle_features.py        # CSV -> data/features/
uv run python scripts/build_scenarios.py --limit 200   # -> data/episodes/ (completo: ~30 min)

# Perfilado y reportes del dataset
uv run python scripts/run_pipeline.py
```

El `--project ..` no es opcional: sin él, `uv` toma `fleet_loading/` como raíz
de proyecto propia y crea un entorno virtual aparte con otra versión de Python.

Los modelos pesados van en extras opcionales (`gbt`, `attention`, `tracking`,
`kedro`, `docs`) para no obligar a instalar TensorFlow, PyTorch y los GBT a
quien solo necesita uno. `torch` se resuelve desde el índice **CPU** de PyTorch:
el transformer se entrena en CPU y las ruedas de CUDA son varios GB inútiles.

## Desarrollo

```bash
just check        # ruff check + ruff format --check + pytest
just docs         # sitio MkDocs en local
just docs-build   # mkdocs build --strict: falla ante cualquier enlace roto
just --list       # todas las recetas
```

Lo mismo que verifica la CI. Las 479 pruebas incluyen 325 del maestro exacto y
las del decodificador, todas validadas por mutación —se comprobó que fallan ante
regresiones deliberadas, no solo que pasan en verde.

La documentación pasa por `mkdocs build --strict` en CI, así que una referencia
a un archivo que ya no existe rompe el build en vez de quedarse ahí.

## Estructura

| Ruta | Qué contiene |
|---|---|
| `src/loading/` | Maestro exacto: búsqueda óptima y generación de episodios |
| `src/modeling/` | Núcleo compartido: canonicalización, tensores por par, decoder con capacidad, métricas y el protocolo de partición |
| `src/pipeline/`, `src/profiler/` | Ingesta, limpieza y perfilado del dataset del SRI |
| `fleet_loading/` | Pipeline Kedro de los modelos XGBoost, LightGBM y transformer |
| `scripts/` | Entradas de línea de comandos |
| `config/` | Clases de vehículo, hiperparámetros del MLP y rutas del perfilado |
| `docs/` | Sitio MkDocs |
| `chat/` | Transcripciones de sesiones de IA (evidencia de la entrega) |

## Datos

**Servicio de Rentas Internas (SRI) del Ecuador**, portal de datos abiertos —
Matriculación Vehicular, vehículos nuevos: <https://www.sri.gob.ec/datasets>.

2017 se descarta: su CSV no trae la columna `FECHA PROCESO`, así que la
cobertura real es 2018-2026.

## Documentación

El índice completo está en [`docs/`](./docs/index.md) y se publica con
`just docs`. Ver también [`docs/git_lfs.md`](./docs/git_lfs.md), que explica por
qué existe el hook que impide commitear los CSV como blobs.
