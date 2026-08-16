"""src/modeling/figures.py

Historial de entrenamiento y figuras, con un solo formato para los seis modelos.

Por qué esto es un módulo y no una función en cada script
---------------------------------------------------------
De los seis modelos, sólo el MLP tenía curvas versionadas. Los otros cinco las
registraban en MLflow y nada más; cuando la base se reinició, las curvas de
XGBoost, LightGBM y el transformer **dejaron de existir** --sus `run_id` ya no
resuelven--. Las matrices de confusión corrían la misma suerte: las tres de
Kedro se escribían bajo `fleet_loading/data/08_reporting/`, que está ignorado, y
los dos clásicos no dibujaban ninguna.

El patrón que sí funcionaba vivía dentro de `scripts/train_mlp.py`, así que no se
podía reutilizar sin copiarlo. Aquí está una sola vez, y cada entrenamiento
escribe en `artifacts/<modelo>/`, que sí se versiona.

El eje viaja en el dato
-----------------------
Los seis modelos convergen sobre ejes distintos: épocas el MLP y el transformer,
rondas de boosting los GBT, árboles el Random Forest, iteraciones de lbfgs la
regresión logística. Rotular «época» una curva de XGBoost es un error fácil y
silencioso, así que `step_unit` se guarda **como columna del CSV** en vez de
quedar en la cabeza de quien dibuja: `plot_curves` lee la unidad del archivo y
rotula el eje con ella.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - sólo para anotaciones
    import matplotlib.figure

# Rótulo humano de cada eje, en el idioma del sitio. La clave es lo que se
# escribe en el CSV; el valor, lo que se pinta.
STEP_UNITS: dict[str, str] = {
    "epoch": "Época",
    "boosting_round": "Ronda de boosting",
    "n_trees": "Árboles en el bosque",
    "lbfgs_iter": "Iteración de lbfgs",
}


@dataclass(frozen=True)
class Presentacion:
    """Cómo se rotula la figura de un modelo.

    Vive aquí y no en cada entrenamiento porque las figuras se dibujan por dos
    caminos --al entrenar y al redibujar con `scripts/report_figures.py`-- y si
    cada uno trajera sus propios rótulos, el mismo archivo diría una cosa u otra
    según quién lo escribió último.
    """

    etiqueta: str
    metrica: tuple[str, str]
    nombre_metrica: str
    nota: str | None = None

    @property
    def titulo(self) -> str:
        return f"Curvas de convergencia — {self.etiqueta}"

    @property
    def titulo_matriz(self) -> str:
        return f"{self.etiqueta} — validación"


# La separación entre las dos curvas de pérdida del MLP NO es sobreajuste, y sin
# decirlo la figura se lee al revés: el entrenamiento aplica `sample_weight` para
# compensar el desbalance de SIN_CAMION y la validación no. Es el único de los
# seis con esta salvedad.
_NOTA_PESOS = (
    "Las dos series no son comparables directamente: el entrenamiento aplica pesos de\n"
    "clase y la validación no. Sin pesos, la pérdida de validación es menor que la de\n"
    "entrenamiento (ver training_report.json → unweighted_loss)."
)

_EXACTITUD_ASIGNACION = "Exactitud cruda de asignación"
_EXACTITUD_OPCION = "Exactitud sobre las filas de opción"

PRESENTACION: dict[str, Presentacion] = {
    "mlp": Presentacion(
        "MLP (Keras)",
        ("raw_assignment_accuracy", "val_raw_assignment_accuracy"),
        _EXACTITUD_ASIGNACION,
        _NOTA_PESOS,
    ),
    "xgboost": Presentacion("XGBoost", ("accuracy", "val_accuracy"), _EXACTITUD_OPCION),
    "lightgbm": Presentacion("LightGBM", ("accuracy", "val_accuracy"), _EXACTITUD_OPCION),
    "attention": Presentacion("Transformer", ("accuracy", "val_accuracy"), _EXACTITUD_ASIGNACION),
    "rf": Presentacion("Random Forest", ("macro_f1", "val_macro_f1"), "F1 macro"),
    "logreg": Presentacion("Regresión logística", ("macro_f1", "val_macro_f1"), "F1 macro"),
}


def plot_model_curves(
    clave: str,
    rows: list[dict[str, float]],
    step_unit: str,
    out_dir: Path,
    steps: list[int] | None = None,
):
    """Dibuja `learning_curves.png` de un modelo con sus rótulos declarados."""
    p = PRESENTACION[clave]
    plot_curves(
        rows,
        step_unit,
        out_dir / "learning_curves.png",
        p.titulo,
        steps=steps,
        metrica=p.metrica if p.metrica[0] in rows[0] else None,
        nombre_metrica=p.nombre_metrica,
        nota=p.nota,
    )


def etiquetas_canonicas(n_labels: int) -> list[str]:
    """`['Sin camión', 'Cam1', ..., 'CamT']` -- el índice 0 es **diferir**.

    `canonicalization.py` reserva el 0 para SIN_CAMION y deja 1..T para los
    camiones por capacidad descendente. Poner «Sin camión» al final --como hacía
    el pipeline Kedro-- corre todos los rótulos una posición.
    """
    return ["Sin camión"] + [f"Cam{i}" for i in range(1, n_labels)]


def _plt():
    """Matplotlib con backend sin pantalla, importado tarde.

    El import cuesta ~0,4 s y estos módulos se cargan en el arranque de cada
    script; sólo quien dibuja lo paga.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


# --- historial ------------------------------------------------------------


def write_history(
    path: Path,
    rows: list[dict[str, Any]],
    step_unit: str,
    steps: list[int] | None = None,
) -> None:
    """Escribe `training_history.csv`: una fila por paso, con la unidad dentro.

    `step` es el valor **en las unidades de `step_unit`**, no el número de fila.
    Para épocas y rondas de boosting coinciden y se numeran desde 1, igual que
    dice la consola (`Epoch 1/50`, no `Epoch 0/50`). Para el Random Forest y la
    regresión logística no coinciden --se mide cada 50 árboles o cada 200
    iteraciones--, así que quien los produce pasa `steps` explícito.

    Poner ahí el índice de fila haría que el eje mintiera por un factor de 50 o
    de 200, que es justo el error que este formato existe para impedir.
    """
    if step_unit not in STEP_UNITS:
        raise ValueError(f"step_unit desconocido: {step_unit!r}. Opciones: {sorted(STEP_UNITS)}")
    if not rows:
        raise ValueError("No hay historial que escribir.")
    if steps is not None and len(steps) != len(rows):
        raise ValueError(f"{len(steps)} pasos para {len(rows)} filas: no cuadran.")

    pasos = steps if steps is not None else list(range(1, len(rows) + 1))
    series = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["step", "step_unit", *series])
        writer.writeheader()
        for paso, row in zip(pasos, rows, strict=True):
            writer.writerow({"step": paso, "step_unit": step_unit, **row})


def read_history(path: Path) -> tuple[list[dict[str, float]], str, list[int]]:
    """`(filas, step_unit, pasos)`. Permite redibujar sin reentrenar."""
    with path.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        raise ValueError(f"{path} no tiene filas.")
    unidad = filas[0]["step_unit"]
    pasos = [int(float(f["step"])) for f in filas]
    datos = [
        {k: float(v) for k, v in f.items() if k not in ("step", "step_unit") and v != ""}
        for f in filas
    ]
    return datos, unidad, pasos


# --- curvas ---------------------------------------------------------------


def plot_curves(
    rows: list[dict[str, float]],
    step_unit: str,
    out_path: Path,
    titulo: str,
    *,
    steps: list[int] | None = None,
    perdida: tuple[str, str] = ("loss", "val_loss"),
    metrica: tuple[str, str] | None = None,
    nombre_metrica: str = "Exactitud",
    nota: str | None = None,
) -> None:
    """Dos paneles: pérdida a la izquierda, métrica de calidad a la derecha.

    Es el formato que ya usaba el MLP, generalizado. Las series ausentes se
    omiten en silencio en vez de fallar: el Random Forest no tiene pérdida de
    validación por árbol y una curva de un solo trazo sigue siendo útil.
    """
    plt = _plt()
    paneles = 1 if metrica is None else 2
    fig, axes = plt.subplots(1, paneles, figsize=(5.5 * paneles, 4.6), squeeze=False)
    pasos = steps if steps is not None else list(range(1, len(rows) + 1))
    eje = STEP_UNITS.get(step_unit, step_unit)

    def trazar(ax, claves: tuple[str, str], titulo_panel: str) -> None:
        for clave, etiqueta in zip(claves, ("entrenamiento", "validación"), strict=True):
            serie = [r[clave] for r in rows if clave in r]
            if serie:
                ax.plot(pasos[: len(serie)], serie, label=etiqueta)
        ax.set_title(titulo_panel)
        ax.set_xlabel(eje)
        ax.legend()
        ax.grid(alpha=0.3)

    trazar(axes[0][0], perdida, "Pérdida")
    if metrica is not None:
        trazar(axes[0][1], metrica, nombre_metrica)

    if nota:
        axes[0][0].text(
            0.5,
            -0.30,
            nota,
            transform=axes[0][0].transAxes,
            ha="center",
            va="top",
            fontsize=7.5,
            style="italic",
        )

    fig.suptitle(titulo)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --- matriz de confusión --------------------------------------------------


def plot_confusion_matrix(
    matrix: list[list[int]],
    labels: list[str],
    titulo: str,
    out_path: Path | None = None,
) -> matplotlib.figure.Figure:
    """Matriz normalizada por fila, con el conteo crudo debajo de la proporción.

    Normalizar por fila no es cosmético: `MOTOCICLETA`/`CAMION_1` concentra dos
    órdenes de magnitud más filas que el resto y en crudo aplasta toda la escala
    de color. Cada celda muestra las dos cifras para que la proporción no oculte
    cuántos casos la sostienen.

    Fila = maestro exacto, columna = predicción, que es el orden en que
    `metrics.confusion()` la construye.

    Devuelve la figura y sólo la guarda si se le da `out_path`: los nodos de
    Kedro la entregan al catálogo, que escribe él mismo.
    """
    plt = _plt()
    m = np.asarray(matrix, dtype=float)
    with np.errstate(invalid="ignore"):
        totales = m.sum(axis=1, keepdims=True)
        norm = np.where(totales > 0, m / np.where(totales > 0, totales, 1.0), 0.0)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicho por el modelo")
    ax.set_ylabel("Maestro exacto")
    ax.set_title(f"{titulo}\nNormalizada por fila; etiquetas canónicas por capacidad")

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j,
                i,
                f"{norm[i, j]:.2f}\n{int(m[i, j]):,}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if norm[i, j] > 0.5 else "black",
            )
    fig.colorbar(im, ax=ax, label="Proporción de la fila")
    fig.tight_layout()
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    return fig
