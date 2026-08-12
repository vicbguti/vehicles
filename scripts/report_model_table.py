"""Genera la tabla comparativa de modelos a partir de las métricas medidas.

La tabla de `docs/index.md` y `docs/metricas.md` se escribía a mano. Por eso
sobrevivió meses diciendo «6.968 episodios, GroupShuffleSplit» después de que el
código pasara al holdout temporal: nada conectaba el texto con los números.

Este script lee los JSON que produce el pipeline y emite el Markdown. Si las
cifras cambian, se vuelve a ejecutar; no se editan a mano.

Uso:
    uv run python scripts/report_model_table.py            # a stdout
    uv run python scripts/report_model_table.py --check    # ¿coincide con docs/?
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

# Salida fresca del pipeline. Está gitignorada: se regenera con `just train-fleet`.
KEDRO_OUT = REPO / "fleet_loading" / "data" / "07_model_output"

# Copia versionada de la última corrida publicada. Es la que lee CI, que no
# entrena, y la que hace que `--check` signifique algo en un clon limpio.
RESULTADOS_PUBLICADOS = REPO / "artifacts" / "fleet_loading" / "results"

MLP_METRICS = REPO / "artifacts" / "mlp" / "metrics.json"

# (etiqueta, archivo, prefijo de las claves dentro del JSON)
FUENTES_KEDRO = [
    ("XGBoost", "xgb_results.json", "xgb"),
    ("LightGBM", "lgb_results.json", "lgb"),
    ("Transformer", "att_results.json", "att"),
]

MARCA_INICIO = "<!-- INICIO tabla generada -->"
MARCA_FIN = "<!-- FIN tabla generada -->"


def _get(d: dict[str, Any], *ruta: str, default: Any = None) -> Any:
    """Acceso anidado tolerante: devuelve `default` si falta cualquier tramo."""
    for k in ruta:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def _fila(
    nombre: str,
    agregados: dict[str, Any],
    acc: float | None,
    f1: float | None,
    latencia: dict[str, Any] | None = None,
) -> str:
    """Una fila de la tabla. Los decimales van con coma: el sitio está en español."""

    def num(x: Any, n: int = 4) -> str:
        return "—" if x is None else f"{float(x):.{n}f}".replace(".", ",")

    def pct(x: Any) -> str:
        return "—" if x is None else f"{float(x):.1f} %".replace(".", ",")

    lat = latencia if latencia is not None else agregados.get("latency", {}) or {}
    return (
        f"| **{nombre}** "
        f"| {num(acc, 3)} "
        f"| {num(f1, 3)} "
        f"| {num(agregados.get('loaded_gap_mean'))} "
        f"| {pct(agregados.get('episodes_matching_teacher_count_pct'))} "
        f"| {pct(agregados.get('cu_utilization_model_pct'))} "
        f"| {num(agregados.get('capacity_violation_rate'), 1)} "
        f"| {num(lat.get('mean_ms'), 2)} / {num(lat.get('p99_ms'), 2)} |"
    )


def construir_tabla() -> str:
    # Se prefiere la salida fresca del pipeline; si no está (clon limpio, CI),
    # se leen los resultados publicados.
    origen = KEDRO_OUT if KEDRO_OUT.exists() else RESULTADOS_PUBLICADOS
    if not origen.exists():
        raise SystemExit(
            f"No hay resultados ni en {KEDRO_OUT} ni en {RESULTADOS_PUBLICADOS}.\n"
            "Ejecuta el pipeline:  just train-fleet"
        )

    filas: list[str] = []
    greedy: dict[str, Any] | None = None
    n_episodios: int | None = None

    for nombre, archivo, prefijo in FUENTES_KEDRO:
        ruta = origen / archivo
        if not ruta.exists():
            print(f"aviso: falta {ruta.name}, se omite {nombre}", file=sys.stderr)
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        operativo = datos.get(f"{prefijo}_operational", {})
        modelo = operativo.get("model", {})
        if greedy is None:
            greedy = operativo.get("greedy")
        n_episodios = n_episodios or modelo.get("n_episodes")
        filas.append(
            _fila(
                nombre,
                modelo,
                datos.get(f"{prefijo}_val_accuracy"),
                datos.get(f"{prefijo}_val_defer_f1"),
            )
        )

    if MLP_METRICS.exists():
        datos = json.loads(MLP_METRICS.read_text(encoding="utf-8"))
        # Puerta de comparabilidad: el MLP solo entra en la tabla si se midió con
        # el mismo protocolo. Es exactamente lo que falló durante meses.
        if datos.get("split_strategy") != "time":
            raise SystemExit(
                f"artifacts/mlp/metrics.json tiene split_strategy="
                f"{datos.get('split_strategy')!r}, no 'time'. Sus cifras no son "
                "comparables con las del pipeline: reentrena el MLP antes de publicar."
            )
        agregados = _get(datos, "model", "val", default={})
        if agregados:
            # La latencia del MLP se deja vacía A PROPÓSITO. `scripts/evaluate_mlp.py`
            # cronometra `model.predict()` + `decode_episode` (inferencia completa,
            # ~43 ms, dominada por la sobrecarga de Keras), mientras que
            # `pairwise.py::measure_latency` cronometra solo `decode_episode`
            # (~0,04 ms). Ponerlas en la misma columna sería publicar dos
            # mediciones distintas como si fueran comparables, que es justo el
            # error que este proyecto acaba de corregir en la partición.
            filas.append(
                _fila(
                    "MLP (Keras)",
                    agregados,
                    agregados.get("raw_assignment_accuracy"),
                    agregados.get("macro_f1"),
                    latencia={},
                )
            )
        greedy = greedy or _get(datos, "baseline_greedy", "val", default=None)

    if greedy:
        filas.append(_fila("Greedy (línea base)", greedy, None, None))

    cabecera = (
        "| Modelo | Exactitud | F1 diferir | Brecha de conteo | Iguala al maestro "
        "| Llenado (CU) | Violación cap. | Latencia media / p99 (ms) |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    pie = (
        f"\n\nMedido sobre la validación del protocolo temporal "
        f"(**{n_episodios or '?'} episodios**, año 2025) contra el maestro exacto.\n\n"
        "La **latencia del MLP se omite a propósito**: `scripts/evaluate_mlp.py` "
        "cronometra la inferencia completa (`model.predict` + decodificación, ~43 ms, "
        "dominada por la sobrecarga de Keras), mientras que el pipeline Kedro cronometra "
        "solo `decode_episode` (~0,04 ms). Son dos mediciones distintas y ponerlas en la "
        "misma columna las haría parecer comparables.\n\n"
        "Tabla generada por `scripts/report_model_table.py` a partir de los JSON medidos. "
        "**No editar a mano**: se regenera, y `--check` lo verifica en CI."
    )
    return MARCA_INICIO + "\n" + cabecera + "\n" + "\n".join(filas) + pie + "\n" + MARCA_FIN


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--check",
        action="store_true",
        help="Falla si la tabla publicada no coincide con las métricas medidas.",
    )
    args = p.parse_args()

    tabla = construir_tabla()
    if not args.check:
        print(tabla)
        return 0

    desincronizados = []
    for doc in (REPO / "docs" / "index.md", REPO / "docs" / "metricas.md"):
        texto = doc.read_text(encoding="utf-8")
        if MARCA_INICIO not in texto:
            continue
        actual = texto[texto.index(MARCA_INICIO) : texto.index(MARCA_FIN) + len(MARCA_FIN)]
        if actual.strip() != tabla.strip():
            desincronizados.append(doc.relative_to(REPO))

    if desincronizados:
        print("Tabla desincronizada en:", ", ".join(str(d) for d in desincronizados))
        print("Regenera con: uv run python scripts/report_model_table.py")
        return 1
    print("La tabla publicada coincide con las métricas medidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
