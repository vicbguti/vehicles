# Recetas de desarrollo. Requiere `just` (https://github.com/casey/just) y `uv`.
# Ver todas:  just --list

default:
    @just --list

# Lo único que necesita un clon nuevo para quedar operativo.
#
# No se usa `git config core.hooksPath .githooks`: apuntaría Git fuera de
# .git/hooks/, que es justo donde `pre-commit install` escribe, y el guard de
# LFS dejaría de correr. En su lugar, pre-commit invoca .githooks/pre-commit
# como hook local (ver .pre-commit-config.yaml).
setup:
    uv sync
    git lfs install --local
    git lfs pull
    uv run pre-commit install

# --- puertas de calidad ---------------------------------------------------

lint:
    uv run ruff check .

format:
    uv run ruff format .

format-check:
    uv run ruff format --check .

test:
    uv run pytest -q

cov:
    uv run pytest --cov --cov-report=term-missing

# Todo lo que CI verifica, en un solo comando.
check: lint format-check test

# --- documentación --------------------------------------------------------

# Puerto 8001 a propósito: el API de distribución ocupa el 8000 (ver src/api/main.py),
# así que `just docs` y la API pueden correr en paralelo.
docs:
    uv run --extra docs mkdocs serve -a 127.0.0.1:8001

docs-build:
    uv run --extra docs mkdocs build --strict

# --- datos y modelos ------------------------------------------------------

# Comprueba que los CSV son datos reales y no punteros LFS sin descargar.
verify-data:
    #!/usr/bin/env bash
    set -euo pipefail
    if head -c 40 data/clean/SRI_Vehiculos_Nuevos_2025.csv | grep -q 'git-lfs'; then
        echo "error: los CSV son punteros LFS. Ejecuta 'git lfs pull'." >&2
        exit 1
    fi
    echo "Datos OK."

features: verify-data
    uv run python scripts/build_vehicle_features.py

# El barrido completo tarda ~30 min; usa --limit para una muestra.
episodes limit="":
    uv run python scripts/build_scenarios.py {{ if limit != "" { "--limit " + limit } else { "" } }}

train-mlp:
    uv run python scripts/train_mlp.py

evaluate-mlp:
    uv run python scripts/evaluate_mlp.py

# Conjuntos de prueba fuera del sobre de entrenamiento (1-4 camiones, 20 vehículos).
# Dos ejes, uno por conjunto; ver docs/modelo/resultados.md sección 6.
extrapolation-trucks n_trucks="5 6" mode="same":
    uv run python scripts/build_extrapolation_set.py --n-trucks {{ n_trucks }} --cap-mode {{ mode }}

# El eje que el recorte MAX_N=20 dejaba sin medir: el 51 % de los manifiestos
# reales lo supera. Reconstruye desde las features, no desde los episodios.
extrapolation-manifest max_n="40":
    uv run python scripts/build_extrapolation_set.py --axis manifest --max-n {{ max_n }}

# Los dos clásicos: flota rellenada a ancho fijo y búsqueda con Optuna.
# Ver docs/modelo/modelos_clasicos.md.
train-rf trials="50":
    uv run python scripts/train_classical.py --model rf --split time --n-trials {{ trials }}

train-logreg trials="50":
    uv run python scripts/train_classical.py --model logreg --split time --n-trials {{ trials }}

# Reajusta los clásicos con los hiperparámetros ya publicados, sin repetir la
# búsqueda: la del RF costó 100 min y 50 intentos. Es lo que hay que correr para
# regenerar artefactos o curvas sin cambiar las cifras publicadas.
refit-rf:
    uv run python scripts/train_classical.py --model rf --split time \
        --refit-from artifacts/rf/training_report.json

refit-logreg:
    uv run python scripts/train_classical.py --model logreg --split time \
        --refit-from artifacts/logreg/training_report.json

# Los tres modelos del pipeline Kedro (XGBoost, LightGBM, transformer).
#
# El `--project ..` no es adorno: sin él, uv toma fleet_loading/ como raíz de
# proyecto propia y crea un entorno virtual aparte. Ver fleet_loading/pyproject.toml.
train-fleet:
    cd fleet_loading && uv run --project .. kedro run

# Un solo nodo, sin reentrenar: las figuras son función pura de las predicciones.
fleet-figures:
    cd fleet_loading && uv run --project .. kedro run --nodes report_confusion_matrices

# Las doce figuras del póster --seis curvas y seis matrices de confusión-- desde
# los CSV y JSON ya guardados. No entrena nada: las curvas se releen de
# `training_history.csv` y las matrices salen de la `confusion_matrix` que cada
# modelo publica en su JSON. Ver docs/metricas.md.
figures:
    uv run python scripts/report_figures.py

mlflow:  # una sola base en la raíz: la comparten el pipeline y train_classical.py
    uv run mlflow ui --backend-store-uri sqlite:///mlflow.db

# Reescribe la tabla comparativa en docs/ desde los JSON medidos. CI verifica
# con --check que lo publicado coincida con lo medido.
model-table:
    uv run python scripts/report_model_table.py --write
