"""Contrato del historial de entrenamiento y de las figuras compartidas.

Lo que se fija aquí no es el aspecto de las gráficas --eso no se puede afirmar
en una prueba-- sino las dos propiedades de las que depende que sean
comparables entre modelos: que la unidad del eje viaje dentro del CSV, y que el
CSV se pueda releer para redibujar sin reentrenar.
"""

from __future__ import annotations

import pytest

from src.modeling.figures import (
    STEP_UNITS,
    plot_confusion_matrix,
    plot_curves,
    read_history,
    write_history,
)


def test_el_historial_lleva_la_unidad_del_eje_en_cada_fila(tmp_path):
    """La razón de ser del formato: una curva de XGBoost no se puede rotular
    «época» por descuido, porque el archivo dice qué es."""
    destino = tmp_path / "training_history.csv"
    write_history(
        destino,
        [{"loss": 0.5, "val_loss": 0.6}, {"loss": 0.4, "val_loss": 0.55}],
        "boosting_round",
    )

    texto = destino.read_text(encoding="utf-8")
    assert texto.splitlines()[0] == "step,step_unit,loss,val_loss"
    assert texto.count("boosting_round") == 2


def test_el_historial_se_relee_tal_cual_se_escribio(tmp_path):
    """Redibujar sin reentrenar es lo que hace `just figures` posible."""
    destino = tmp_path / "h.csv"
    filas = [{"loss": 0.5, "acc": 0.7}, {"loss": 0.25, "acc": 0.9}]
    write_history(destino, filas, "epoch")

    releidas, unidad, _ = read_history(destino)
    assert unidad == "epoch"
    assert releidas == filas


def test_el_paso_va_en_las_unidades_del_eje_no_en_numero_de_fila(tmp_path):
    """El Random Forest mide cada 50 árboles: si el CSV guardara 1, 2, 3… el eje
    mentiría por un factor de 50 y la gráfica diría que 500 árboles son 10.

    Es el mismo error que `step_unit` existe para impedir, un nivel más abajo:
    de nada sirve rotular «árboles» un eje cuyos valores son índices de fila.
    """
    destino = tmp_path / "h.csv"
    write_history(
        destino,
        [{"loss": 0.9}, {"loss": 0.6}, {"loss": 0.5}],
        "n_trees",
        steps=[50, 100, 150],
    )

    _, unidad, pasos = read_history(destino)
    assert (unidad, pasos) == ("n_trees", [50, 100, 150])


def test_unos_pasos_que_no_cuadran_con_las_filas_fallan(tmp_path):
    with pytest.raises(ValueError, match="no cuadran"):
        write_history(tmp_path / "h.csv", [{"loss": 1.0}], "n_trees", steps=[50, 100])


def test_los_pasos_se_numeran_desde_uno(tmp_path):
    """Sin `steps`, el eje son épocas o rondas y empieza en 1: la consola dice
    `Epoch 1/50`, no `Epoch 0/50`, y el CSV debe decir lo mismo."""
    destino = tmp_path / "h.csv"
    write_history(destino, [{"loss": 1.0}, {"loss": 0.5}], "epoch")

    assert [linea.split(",")[0] for linea in destino.read_text().splitlines()[1:]] == ["1", "2"]


def test_una_unidad_desconocida_falla_en_vez_de_colarse(tmp_path):
    """Sin esto, un `step_unit="iteracion"` cualquiera acabaría rotulando un eje
    con una cadena que nadie definió."""
    with pytest.raises(ValueError, match="step_unit desconocido"):
        write_history(tmp_path / "h.csv", [{"loss": 1.0}], "iteracion")


def test_las_seis_unidades_que_usan_los_modelos_estan_declaradas():
    assert set(STEP_UNITS) == {"epoch", "boosting_round", "n_trees", "lbfgs_iter"}


def test_dibujar_curvas_produce_un_archivo(tmp_path):
    destino = tmp_path / "learning_curves.png"
    plot_curves(
        [{"loss": 0.5, "val_loss": 0.6, "acc": 0.7, "val_acc": 0.68}] * 3,
        "epoch",
        destino,
        "prueba",
        metrica=("acc", "val_acc"),
    )
    assert destino.stat().st_size > 0


def test_una_curva_sin_serie_de_validacion_sigue_dibujandose(tmp_path):
    """El Random Forest no tiene pérdida de validación por árbol; media curva
    sigue siendo información y no debe hacer fallar el reporte."""
    destino = tmp_path / "c.png"
    plot_curves([{"loss": 0.5}, {"loss": 0.3}], "n_trees", destino, "sólo entrenamiento")
    assert destino.stat().st_size > 0


def test_la_matriz_se_normaliza_por_fila_sin_dividir_por_cero(tmp_path):
    """Una clase que el maestro nunca usó deja una fila entera a cero. Antes de
    normalizar hay que mirar esa fila, no dividir y confiar en el NaN."""
    destino = tmp_path / "cm.png"
    fig = plot_confusion_matrix(
        [[5, 1, 0], [2, 8, 0], [0, 0, 0]],
        ["Sin camión", "Cam1", "Cam2"],
        "prueba",
        destino,
    )
    assert destino.stat().st_size > 0
    # La fila vacía se pinta como ceros, no como NaN: un NaN se dibuja en blanco
    # y se confunde con «proporción 0», que es una afirmación distinta.
    assert fig.axes[0].images[0].get_array()[2].tolist() == [0.0, 0.0, 0.0]


def test_la_matriz_no_se_guarda_si_no_se_pide(tmp_path):
    """Los nodos de Kedro entregan la figura al catálogo, que escribe él."""
    fig = plot_confusion_matrix([[1, 0], [0, 1]], ["a", "b"], "prueba")
    assert fig is not None
    assert list(tmp_path.iterdir()) == []
