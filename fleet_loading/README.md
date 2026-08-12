# Pipeline Kedro — XGBoost, LightGBM y transformer

Entrena los tres modelos que no son el MLP. No es un proyecto independiente:
consume el núcleo compartido de `src/modeling/` (canonicalización, tensores por
par, decodificador con capacidad, métricas y **la partición**), que es lo que
hace que sus cifras sean comparables con las del MLP.

## Ejecutar

Desde la raíz del repositorio. **No hay entorno virtual por subproyecto**: hay
un solo `pyproject.toml` y un solo `uv.lock`.

```bash
uv sync --extra gbt --extra attention --extra tracking --extra kedro
cd fleet_loading && uv run kedro run
```

Un solo nodo, sin reentrenar:

```bash
uv run kedro run --nodes report_confusion_matrices
```

## Estructura

| Ruta | Qué contiene |
|---|---|
| `conf/base/catalog.yml` | Entradas y salidas. Rutas **relativas**: antes eran absolutas a la máquina de un integrante y `kedro run` no arrancaba en ningún otro sitio |
| `conf/base/parameters.yml` | Hiper-parámetros de los tres modelos y la partición temporal compartida |
| `src/fleet_loading/pipelines/training/nodes.py` | Los seis nodos |
| `src/fleet_loading/pipelines/training/pairwise.py` | El adaptador al núcleo de `src/modeling` |
| `src/fleet_loading/pipelines/training/attention_model.py` | El transformer en PyTorch |
| `data/` | Salidas intermedias del pipeline (gitignoradas) |

La documentación completa —nodos, diseño por pares y por qué no hay número de
camiones fijado— está en [`docs/pipeline_kedro.md`](../docs/pipeline_kedro.md).

## MLflow

```bash
uv run --extra tracking mlflow ui --backend-store-uri sqlite:///mlflow.db
```

La base está en la raíz del repositorio, no aquí.
