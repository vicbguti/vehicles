#!/usr/bin/env python3
"""Redibuja las doce figuras de los seis modelos sin reentrenar ninguno.

Seis curvas de convergencia y seis matrices de confusión. Ninguna se calcula
aquí: las curvas se releen de `training_history.csv` --que ya trae su
`step_unit`-- y las matrices salen de la `confusion_matrix` que cada modelo
publica en su propio JSON. Este script sólo dibuja.

Que sea posible es la propiedad que importa. Antes las curvas de XGBoost,
LightGBM y el transformer sólo existían dentro de MLflow, y cuando la base se
reinició hubo que **reentrenar** para recuperarlas. Y las matrices del pipeline
se escribían bajo `fleet_loading/data/08_reporting/`, que está en `.gitignore`.
Ahora el dato de cada figura vive versionado junto al modelo, así que cambiar un
color, un rótulo o el tamaño de letra para el póster cuesta segundos.

También sirve de comprobación cruzada: la matriz que se dibuja es exactamente la
que sostiene el `f1_defer` de la tabla comparativa. Si una figura y una fila no
coincidieran, es que una de las dos está leyendo otra cosa.

Uso (desde la raíz del repositorio):
    uv run python scripts/report_figures.py
    uv run python scripts/report_figures.py --solo mlp rf
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.modeling.figures import (  # noqa: E402
    PRESENTACION,
    etiquetas_canonicas,
    plot_confusion_matrix,
    plot_model_curves,
    read_history,
)

ARTIFACTS = REPO_ROOT / "artifacts"

# Dónde vive cada modelo y de qué JSON sale su matriz de confusión de VALIDACIÓN.
# Los rótulos NO están aquí: los declara `PRESENTACION` en src/modeling/figures.py,
# el mismo registro que usan los entrenamientos, para que una figura diga lo
# mismo la escriba quien la escriba.
#
# La partición es siempre validación: es la que publica la tabla comparativa y la
# única sobre la que las seis figuras son comparables entre sí.
MODELOS = (
    ("mlp", ARTIFACTS / "mlp", "metrics.json", ("model", "val")),
    ("xgboost", ARTIFACTS / "fleet_loading" / "xgboost", None, ("xgb_operational", "model")),
    ("lightgbm", ARTIFACTS / "fleet_loading" / "lightgbm", None, ("lgb_operational", "model")),
    ("attention", ARTIFACTS / "fleet_loading" / "attention", None, ("att_operational", "model")),
    ("rf", ARTIFACTS / "rf", "training_report.json", ("domain_metrics", "val")),
    ("logreg", ARTIFACTS / "logreg", "training_report.json", ("domain_metrics", "val")),
)

# Los tres modelos de Kedro comparten un JSON de resultados por prefijo.
RESULTADOS_KEDRO = {
    "xgboost": ARTIFACTS / "fleet_loading" / "results" / "xgb_results.json",
    "lightgbm": ARTIFACTS / "fleet_loading" / "results" / "lgb_results.json",
    "attention": ARTIFACTS / "fleet_loading" / "results" / "att_results.json",
}


def _agregados(clave: str, out_dir: Path, archivo: str | None, ruta: tuple[str, ...]) -> dict:
    """El bloque de validación del JSON del modelo, o `{}` si no está."""
    origen = RESULTADOS_KEDRO[clave] if archivo is None else out_dir / archivo
    if not origen.exists():
        return {}
    datos = json.loads(origen.read_text(encoding="utf-8"))
    for tramo in ruta:
        if not isinstance(datos, dict) or tramo not in datos:
            return {}
        datos = datos[tramo]
    return datos


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--solo",
        nargs="+",
        choices=[m[0] for m in MODELOS],
        help="Redibuja sólo estos modelos. Por omisión, los seis.",
    )
    args = p.parse_args()
    pedidos = set(args.solo) if args.solo else {m[0] for m in MODELOS}

    hechas, faltan = 0, []
    for clave, out_dir, archivo, ruta in MODELOS:
        if clave not in pedidos:
            continue
        etiqueta = PRESENTACION[clave].etiqueta

        historial = out_dir / "training_history.csv"
        if historial.exists():
            filas, step_unit, pasos = read_history(historial)
            plot_model_curves(clave, filas, step_unit, out_dir, steps=pasos)
            print(f"  {etiqueta:<22} curva ({step_unit}, {len(filas)} pasos)")
            hechas += 1
        else:
            faltan.append(f"{etiqueta}: falta {historial.relative_to(REPO_ROOT)}")

        matriz = _agregados(clave, out_dir, archivo, ruta).get("confusion_matrix")
        if matriz:
            plot_confusion_matrix(
                matriz,
                etiquetas_canonicas(len(matriz)),
                PRESENTACION[clave].titulo_matriz,
                out_dir / "confusion_matrix.png",
            )
            print(f"  {etiqueta:<22} matriz {len(matriz)}x{len(matriz)}")
            hechas += 1
        else:
            faltan.append(f"{etiqueta}: sin confusion_matrix en su JSON de métricas")

    print(f"\n{hechas} figuras escritas.")
    if faltan:
        # No es un error: un clon recién hecho puede no tener todos los modelos
        # entrenados. Pero se dice cuál falta y por qué, porque el póster las
        # necesita todas.
        print("\nSin regenerar (hay que entrenar o evaluar ese modelo primero):", file=sys.stderr)
        for f in faltan:
            print(f"  - {f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
