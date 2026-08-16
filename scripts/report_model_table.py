"""Genera la tabla comparativa de modelos a partir de las métricas medidas.

La tabla de `docs/index.md` y `docs/metricas.md` se escribía a mano. Por eso
sobrevivió meses diciendo «6.968 episodios, GroupShuffleSplit» después de que el
código pasara al holdout temporal: nada conectaba el texto con los números.

Este script lee los JSON que produce el pipeline y emite el Markdown. Si las
cifras cambian, se vuelve a ejecutar; no se editan a mano.

Dos ejes de comparabilidad, no uno
----------------------------------
El fallo de la partición motivó `_exigir_protocolo_temporal`, que vigila **con
qué datos** se midió cada fila. Faltaba la otra mitad: **qué** se midió. La
columna «F1 diferir» se llenaba con `<prefijo>_val_defer_f1` para tres modelos y
con `macro_f1` para los otros tres --dos métricas distintas, del mismo orden de
magnitud, bajo el mismo encabezado--. Encima la fila del transformer venía de un
argmax crudo tomado en su mejor época, cuando las demás eran post-decodificador,
y por eso aparecía como el modelo más exacto del cuadro.

Las dos causas eran la misma: `_fila` aceptaba lo que hubiera con `.get()`. Ahora
**todas las filas leen del mismo bloque** --los agregados que produce
`src.modeling.metrics.aggregate()`, únicos para los seis modelos-- y
`_exigir_misma_metrica` rechaza cualquier fila que no traiga exactamente las
mismas claves que las demás. Una fila incompleta falla ruidosamente en vez de
publicarse con otra métrica en su lugar.

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

# Los clásicos de `scripts/train_classical.py`. Traen un tercer formato de
# archivo, pero no una tercera implementación de las métricas: sus agregados
# salen de `metrics.aggregate()`, igual que los del MLP y los de Kedro, así que
# `domain_metrics["val"]` tiene exactamente las mismas claves que el
# `model["val"]` del MLP y `_fila` las lee sin cambios.
FUENTES_CLASICAS = [
    ("Random Forest", "rf"),
    ("Regresión logística", "logreg"),
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


def _exigir_protocolo_temporal(datos: dict[str, Any], fuente: str) -> None:
    """Puerta de comparabilidad 1/2: nadie entra a la tabla con otra partición.

    Es exactamente el fallo que esta tabla publicó durante meses, así que se
    verifica por archivo en vez de confiar en que quien entrena se acuerde.

    La comprobación cubre las seis fuentes. Durante un tiempo las tres de Kedro
    quedaban exentas de hecho, no de derecho: sus JSON no traían la clave, así
    que `datos.get(...)` habría fallado siempre y en vez de eso ni se llamaba.
    Ahora los nodos la emiten (`nodes.py`, `attention_model.py`).
    """
    if datos.get("split_strategy") != "time":
        raise SystemExit(
            f"{fuente} tiene split_strategy={datos.get('split_strategy')!r}, no 'time'. "
            "Sus cifras no son comparables con las del resto de la tabla: "
            "reentrena con --split time antes de publicar."
        )


# Lo que publica cada columna. Todas salen de `metrics.aggregate()`, así que una
# fuente a la que le falte una es una fuente medida de otra forma, no una fuente
# incompleta: por eso la ausencia es un error y no un hueco que se rellena.
METRICAS_PUBLICADAS = (
    "raw_assignment_accuracy",
    "f1_defer",
    "macro_f1",
    "loaded_gap_mean",
    "episodes_matching_teacher_count_pct",
    "cu_utilization_model_pct",
    "capacity_violation_rate",
)


def _exigir_misma_metrica(nombre: str, agregados: dict[str, Any]) -> None:
    """Puerta de comparabilidad 2/2: todas las filas miden exactamente lo mismo.

    Sustituye al `.get()` tolerante que devolvía `None` --o peor, la métrica de
    al lado-- cuando una fuente no traía una clave. Es el mecanismo por el que
    «F1 diferir» acabó conteniendo dos cosas distintas sin que nada avisara.
    """
    faltan = [k for k in METRICAS_PUBLICADAS if k not in agregados]
    if faltan:
        raise SystemExit(
            f"{nombre} no aporta {', '.join(faltan)}. Todas las filas de la tabla se leen "
            "del mismo bloque de agregados, así que una clave ausente significa que esa "
            "fila se midió de otra forma y no es comparable. Reentrena o reevalúa para "
            "regenerar su JSON con `src.modeling.metrics.aggregate()` al día."
        )


def _ms(x: Any) -> str:
    """Latencia para la prosa del pie, con la coma decimal del sitio."""
    if x is None:
        return "sin medir"
    return (f"~{float(x):.2f} ms" if float(x) < 1 else f"~{float(x):.0f} ms").replace(".", ",")


def _fila(nombre: str, agregados: dict[str, Any], latencia: dict[str, Any] | None = None) -> str:
    """Una fila de la tabla. Los decimales van con coma: el sitio está en español.

    Recibe **sólo** el bloque de agregados. Antes tomaba además `acc` y `f1`
    sueltos, que era la puerta por la que cada fuente metía su propia métrica.
    """
    _exigir_misma_metrica(nombre, agregados)

    def num(x: Any, n: int = 4) -> str:
        return "—" if x is None else f"{float(x):.{n}f}".replace(".", ",")

    def pct(x: Any) -> str:
        return "—" if x is None else f"{float(x):.1f} %".replace(".", ",")

    lat = latencia if latencia is not None else agregados.get("latency", {}) or {}
    return (
        f"| **{nombre}** "
        f"| {num(agregados['raw_assignment_accuracy'], 3)} "
        f"| {num(agregados['f1_defer'], 3)} "
        f"| {num(agregados['macro_f1'], 3)} "
        f"| {num(agregados['loaded_gap_mean'])} "
        f"| {pct(agregados['episodes_matching_teacher_count_pct'])} "
        f"| {pct(agregados['cu_utilization_model_pct'])} "
        f"| {num(agregados['capacity_violation_rate'], 1)} "
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
    # Las dos latencias del pie se leen de los JSON, no se escriben a mano: son
    # cifras medidas y el pie decía «~43 ms» meses después de que dejara de
    # serlo. Es el mismo motivo por el que existe este script.
    lat_mlp: float | None = None
    lat_decoder: float | None = None

    for nombre, archivo, prefijo in FUENTES_KEDRO:
        ruta = origen / archivo
        if not ruta.exists():
            print(f"aviso: falta {ruta.name}, se omite {nombre}", file=sys.stderr)
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        _exigir_protocolo_temporal(datos, f"artifacts/fleet_loading/results/{archivo}")
        # `<prefijo>_operational.model`, igual que el MLP y los clásicos. Las
        # claves sueltas `<prefijo>_rawrow_*` y `att_rawargmax_best_*` que hay al
        # lado son diagnóstico del clasificador antes de decodificar, y una de
        # ellas --la del transformer-- ni siquiera corresponde a los pesos
        # guardados: es la mejor época según validación.
        operativo = datos.get(f"{prefijo}_operational", {})
        modelo = operativo.get("model", {})
        if greedy is None:
            greedy = operativo.get("greedy")
        n_episodios = n_episodios or modelo.get("n_episodes")
        lat_decoder = lat_decoder or _get(modelo, "latency", "mean_ms")
        filas.append(_fila(nombre, modelo))

    if MLP_METRICS.exists():
        datos = json.loads(MLP_METRICS.read_text(encoding="utf-8"))
        _exigir_protocolo_temporal(datos, "artifacts/mlp/metrics.json")
        agregados = _get(datos, "model", "val", default={})
        if agregados:
            # La latencia del MLP se deja vacía A PROPÓSITO. `scripts/evaluate_mlp.py`
            # cronometra `model.predict()` + `decode_episode` (inferencia completa,
            # ~43 ms, dominada por la sobrecarga de Keras), mientras que
            # `pairwise.py::measure_latency` cronometra solo `decode_episode`
            # (~0,04 ms). Ponerlas en la misma columna sería publicar dos
            # mediciones distintas como si fueran comparables, que es justo el
            # error que este proyecto acaba de corregir en la partición.
            filas.append(_fila("MLP (Keras)", agregados, latencia={}))
        lat_mlp = _get(datos, "inference_latency_per_manifest", "mean_ms")
        greedy = greedy or _get(datos, "baseline_greedy", "val", default=None)

    for nombre, modelo in FUENTES_CLASICAS:
        ruta = REPO / "artifacts" / modelo / "training_report.json"
        if not ruta.exists():
            print(f"aviso: falta {ruta.relative_to(REPO)}, se omite {nombre}", file=sys.stderr)
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        _exigir_protocolo_temporal(datos, str(ruta.relative_to(REPO)))
        agregados = _get(datos, "domain_metrics", "val", default={})
        if agregados:
            # Sin latencia, por el mismo criterio que el MLP: `train_classical.py`
            # no la cronometra, y una celda vacía dice eso mejor que un número
            # medido de otra forma.
            filas.append(_fila(nombre, agregados, latencia={}))
        n_episodios = n_episodios or agregados.get("n_episodes")
        greedy = greedy or _get(datos, "greedy_baseline_val", default=None)

    if greedy:
        # El greedy sale del mismo `aggregate()`, así que sus columnas de
        # clasificación ya no van vacías: eran «—» sólo porque el camino de
        # lectura anterior no las tenía a mano. Verlas importa --0,18 de F1 macro
        # contra ~0,79-- porque es la distancia que el aprendizaje cubre.
        filas.append(_fila("Greedy (línea base)", greedy))

    cabecera = (
        "| Modelo | Exactitud | F1 diferir | F1 macro | Brecha de conteo | Iguala al maestro "
        "| Llenado (CU) | Violación cap. | Latencia media / p99 (ms) |\n"
        "|---|---|---|---|---|---|---|---|---|"
    )
    pie = (
        f"\n\nMedido sobre la validación del protocolo temporal "
        f"(**{n_episodios or '?'} episodios**, año 2025) contra el maestro exacto. "
        "Las nueve columnas salen del mismo bloque de agregados de "
        "`src/modeling/metrics.py`, **después del decodificador**, para los seis "
        "modelos y para el greedy.\n\n"
        "**F1 diferir** y **F1 macro** van en columnas separadas porque son métricas "
        "distintas y no intercambiables: la primera mide la clase minoritaria "
        "—dejar un vehículo en el andén—, la segunda promedia las cinco clases y "
        "por eso sale ~0,17 más alta. Cualquiera de las dos se puede reconstruir "
        "desde la matriz de confusión que publica cada modelo en su JSON.\n\n"
        "La **latencia se omite a propósito** en el MLP, Random Forest y la regresión "
        "logística. `scripts/evaluate_mlp.py` cronometra la inferencia completa "
        f"(`model.predict` + decodificación, {_ms(lat_mlp)}, dominada por la sobrecarga "
        f"de Keras), el pipeline Kedro cronometra solo `decode_episode` ({_ms(lat_decoder)}) y "
        "`scripts/train_classical.py` no la cronometra. Son mediciones distintas y "
        "ponerlas en la misma columna las haría parecer comparables.\n\n"
        "Tabla generada por `scripts/report_model_table.py` a partir de los JSON medidos. "
        "**No editar a mano**: se regenera con `--write`, y `--check` lo verifica en CI."
    )
    return MARCA_INICIO + "\n" + cabecera + "\n" + "\n".join(filas) + pie + "\n" + MARCA_FIN


DOCS_CON_TABLA = ("index.md", "metricas.md")


def _paginas() -> list[Path]:
    return [REPO / "docs" / nombre for nombre in DOCS_CON_TABLA]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    modo = p.add_mutually_exclusive_group()
    modo.add_argument(
        "--check",
        action="store_true",
        help="Falla si la tabla publicada no coincide con las métricas medidas.",
    )
    modo.add_argument(
        "--write",
        action="store_true",
        help="Reescribe la tabla en docs/ entre las marcas. Es la forma de regenerarla.",
    )
    args = p.parse_args()

    tabla = construir_tabla()

    if args.write:
        # Sustituir entre marcas en vez de copiar a mano: el pegado manual es
        # justo el eslabón por el que la tabla se quedaba vieja.
        for doc in _paginas():
            texto = doc.read_text(encoding="utf-8")
            if MARCA_INICIO not in texto:
                print(f"aviso: {doc.relative_to(REPO)} no tiene marcas, se omite", file=sys.stderr)
                continue
            inicio = texto.index(MARCA_INICIO)
            fin = texto.index(MARCA_FIN) + len(MARCA_FIN)
            doc.write_text(texto[:inicio] + tabla + texto[fin:], encoding="utf-8")
            print(f"escrita en {doc.relative_to(REPO)}")
        return 0

    if not args.check:
        print(tabla)
        return 0

    desincronizados = []
    for doc in _paginas():
        texto = doc.read_text(encoding="utf-8")
        if MARCA_INICIO not in texto:
            continue
        actual = texto[texto.index(MARCA_INICIO) : texto.index(MARCA_FIN) + len(MARCA_FIN)]
        if actual.strip() != tabla.strip():
            desincronizados.append(doc.relative_to(REPO))

    if desincronizados:
        print("Tabla desincronizada en:", ", ".join(str(d) for d in desincronizados))
        print("Regenera con: uv run python scripts/report_model_table.py --write")
        return 1
    print("La tabla publicada coincide con las métricas medidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
