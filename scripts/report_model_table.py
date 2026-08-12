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
KEDRO_OUT = REPO / "fleet_loading" / "data" / "07_model_output"
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


def _fila(nombre: str, agregados: dict[str, Any], acc: float | None, f1: float | None) -> str:
    def pct(x: Any) -> str:
        return "—" if x is None else f"{float(x):.1f} %"

    def num(x: Any, n: int = 4) -> str:
        return "—" if x is None else f"{float(x):.{n}f}"

    lat = agregados.get("latency", {})
    return (
        f"| **{nombre}** "
        f"| {num(acc, 3) if acc is not None else '—'} "
        f"| {num(f1, 3) if f1 is not None else '—'} "
        f"| {num(agregados.get('loaded_gap_mean'))} "
        f"| {pct(agregados.get('episodes_matching_teacher_count_pct'))} "
        f"| {pct(agregados.get('cu_utilization_model_pct'))} "
        f"| {num(agregados.get('capacity_violation_rate'), 1)} "
        f"| {num(lat.get('mean_ms'), 2)} / {num(lat.get('p99_ms'), 2)} |"
    )


def construir_tabla() -> str:
    if not KEDRO_OUT.exists():
        raise SystemExit(
            f"No existe {KEDRO_OUT}. Ejecuta el pipeline primero:\n"
            "    cd fleet_loading && uv run --project .. kedro run"
        )

    filas: list[str] = []
    greedy: dict[str, Any] | None = None
    n_episodios: int | None = None

    for nombre, archivo, prefijo in FUENTES_KEDRO:
        ruta = KEDRO_OUT / archivo
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
        agregados = _get(datos, "val", "model") or _get(datos, "model") or {}
        if agregados:
            filas.append(_fila("MLP (Keras)", agregados, None, None))

    if greedy:
        filas.append(_fila("Greedy (línea base)", greedy, None, None))

    cabecera = (
        "| Modelo | Exactitud | F1 diferir | Brecha de conteo | Iguala al maestro "
        "| Llenado (CU) | Violación cap. | Latencia media / p99 (ms) |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    pie = (
        f"\n\nMedido sobre la partición de validación del protocolo temporal "
        f"({n_episodios or '?'} episodios, año 2025) contra el maestro exacto. "
        "Generado por `scripts/report_model_table.py`; no editar a mano."
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
