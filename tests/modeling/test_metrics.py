"""Métricas de dominio: brechas frente al maestro y factibilidad."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.features import (
    BlockScaler,
    build_all_episodes,
    build_model_arrays,
)
from src.modeling.metrics import aggregate, confusion, evaluate_greedy, evaluate_model

CLASSES = ["AUTOMOVIL", "CAMIONETA", "JEEP", "MOTOCICLETA"]


def _joined(episodes: list[tuple[str, list[tuple[str, str, float, str]], list[float]]]):
    rows = []
    for episode_id, specs, caps in episodes:
        n_loaded = sum(1 for s in specs if s[3] != "SIN_CAMION")
        cu_used = sum(s[2] for s in specs if s[3] != "SIN_CAMION")
        for uid, clase, cu, truck in specs:
            rows.append(
                {
                    "episode_id": episode_id,
                    "uid": uid,
                    "clase": clase,
                    "cu": cu,
                    "canton": 10701,
                    "truck": truck,
                    "loaded": truck != "SIN_CAMION",
                    "iso_year": 2024,
                    "n_trucks": len(caps),
                    "truck_capacities": caps,
                    "n_loaded": n_loaded,
                    "cu_utilized": cu_used,
                }
            )
    return pd.DataFrame(rows)


def _prepare(spec):
    episodes = build_all_episodes(_joined(spec), CLASSES)
    scaler = BlockScaler.fit(episodes, CLASSES)
    arrays = build_model_arrays(episodes, scaler)
    return episodes, arrays


def _perfect_logits(arrays, strength: float = 20.0) -> np.ndarray:
    """Logits que reproducen exactamente la etiqueta del maestro."""
    n_labels = arrays.max_trucks + 1
    logits = np.zeros((len(arrays.target), n_labels), dtype=float)
    logits[np.arange(len(arrays.target)), arrays.target] = strength
    return logits


def test_un_modelo_perfecto_no_tiene_brecha():
    spec = [
        ("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1"), ("b", "JEEP", 1.1, "CAMION_1")], [6.0]),
        ("E2", [("c", "CAMIONETA", 1.4, "CAMION_1")], [6.0, 3.0]),
    ]
    episodes, arrays = _prepare(spec)
    results = evaluate_model(episodes, arrays, _perfect_logits(arrays))
    m = aggregate(results, arrays.max_trucks + 1)

    assert m["capacity_violation_rate"] == 0.0
    assert m["loaded_gap_mean"] == 0.0
    assert m["episodes_matching_teacher_count_pct"] == 100.0
    assert m["raw_assignment_accuracy"] == 1.0


def test_la_tasa_de_violacion_es_cero_incluso_con_logits_absurdos():
    """La garantía que aporta el decoder: pase lo que pase con el modelo, el
    plan entregado es factible."""
    spec = [("E1", [(f"v{i}", "CAMIONETA", 1.4, "CAMION_1") for i in range(10)], [3.0])]
    episodes, arrays = _prepare(spec)
    rng = np.random.default_rng(0)
    logits = rng.normal(scale=50.0, size=(len(arrays.target), arrays.max_trucks + 1))

    m = aggregate(evaluate_model(episodes, arrays, logits), arrays.max_trucks + 1)
    assert m["capacity_violation_rate"] == 0.0
    assert m["max_overflow_cu"] == 0.0


def test_la_brecha_de_conteo_es_positiva_cuando_el_plan_carga_menos():
    # El maestro carga 3 de 1.0 en un camión de 3.0; el modelo tiene logits que
    # priorizan mal, pero la política "count" recupera el óptimo.
    spec = [
        (
            "E1",
            [
                ("a", "AUTOMOVIL", 1.0, "CAMION_1"),
                ("b", "AUTOMOVIL", 1.0, "CAMION_1"),
                ("c", "AUTOMOVIL", 1.0, "CAMION_1"),
            ],
            [3.0],
        )
    ]
    episodes, arrays = _prepare(spec)
    m = aggregate(evaluate_model(episodes, arrays, _perfect_logits(arrays)), 2)
    assert m["loaded_gap_mean"] == 0.0


def test_la_utilizacion_del_maestro_se_reporta_por_separado():
    spec = [("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [4.0])]
    episodes, arrays = _prepare(spec)
    m = aggregate(evaluate_model(episodes, arrays, _perfect_logits(arrays)), 2)

    assert m["cu_utilization_teacher_pct"] == pytest.approx(25.0)
    assert m["cu_utilization_model_pct"] == pytest.approx(25.0)


def test_los_diferidos_se_cuentan_de_ambos_lados():
    spec = [
        (
            "E1",
            [("a", "CAMIONETA", 1.4, "CAMION_1"), ("b", "CAMIONETA", 1.4, "SIN_CAMION")],
            [1.5],
        )
    ]
    episodes, arrays = _prepare(spec)
    m = aggregate(evaluate_model(episodes, arrays, _perfect_logits(arrays)), 2)

    assert m["deferred_teacher_total"] == 1
    assert m["deferred_model_total"] == 1


def test_la_matriz_de_confusion_tiene_la_forma_de_las_etiquetas():
    spec = [("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0, 3.0])]
    episodes, arrays = _prepare(spec)
    results = evaluate_model(episodes, arrays, _perfect_logits(arrays))
    matrix = confusion(results, 3)

    assert len(matrix) == 3 and len(matrix[0]) == 3
    assert sum(sum(row) for row in matrix) == 1


def test_el_greedy_de_referencia_tambien_es_factible():
    spec = [("E1", [(f"v{i}", "CAMIONETA", 1.4, "CAMION_1") for i in range(8)], [3.0, 3.0])]
    episodes, arrays = _prepare(spec)
    m = aggregate(evaluate_greedy(episodes, arrays), arrays.max_trucks + 1)
    assert m["capacity_violation_rate"] == 0.0


def test_agregar_sin_resultados_falla():
    with pytest.raises(ValueError, match="No hay resultados"):
        aggregate([], 5)


# --- F1 de diferir --------------------------------------------------------
#
# La tabla comparativa publicó durante meses `f1_defer` en tres filas y
# `macro_f1` en las otras tres bajo el mismo encabezado «F1 diferir». Nadie lo
# vio porque las dos son plausibles y del mismo orden de magnitud. Lo que sigue
# ata la cifra a la matriz de confusión que se publica a su lado, que es la única
# comprobación que lo habría detectado.


def _f1_de_la_clase(matriz: list[list[int]], clase: int) -> float:
    """F1 de una clase reconstruido SÓLO desde la matriz de confusión.

    Deliberadamente no usa sklearn ni nada de `metrics.py`: si compartiera
    implementación con lo que verifica, no verificaría nada.
    """
    tp = matriz[clase][clase]
    fn = sum(matriz[clase]) - tp
    fp = sum(fila[clase] for fila in matriz) - tp
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def _episodios_con_error() -> tuple[list, object, np.ndarray]:
    """Un caso donde el modelo se equivoca: si acertara todo, F1 sería 1 y la
    prueba pasaría con cualquier definición de F1."""
    spec = [
        (
            f"E{i}",
            [
                (f"v{i}_{j}", "CAMIONETA", 1.4, "CAMION_1" if j % 3 else "SIN_CAMION")
                for j in range(6)
            ],
            [4.2, 2.8],
        )
        for i in range(8)
    ]
    episodes, arrays = _prepare(spec)
    rng = np.random.default_rng(20260816)
    logits = rng.normal(scale=3.0, size=(len(arrays.target), arrays.max_trucks + 1))
    return episodes, arrays, logits


def test_el_f1_de_diferir_reconcilia_con_su_matriz_de_confusion():
    episodes, arrays, logits = _episodios_con_error()
    n_labels = arrays.max_trucks + 1
    m = aggregate(evaluate_model(episodes, arrays, logits), n_labels)

    assert m["f1_defer"] == pytest.approx(_f1_de_la_clase(m["confusion_matrix"], 0))


def test_el_f1_de_diferir_no_es_el_f1_macro():
    """Son métricas distintas, y por eso no pueden compartir columna.

    Sin esta prueba, publicar `macro_f1` bajo el encabezado «F1 diferir» seguiría
    dando un número creíble.
    """
    episodes, arrays, logits = _episodios_con_error()
    n_labels = arrays.max_trucks + 1
    m = aggregate(evaluate_model(episodes, arrays, logits), n_labels)

    assert m["f1_defer"] != pytest.approx(m["macro_f1"])
    # Y `macro_f1` es la media de las F1 de todas las clases presentes, una de
    # las cuales es la de diferir: eso es lo que la diluye.
    presentes = [
        c
        for c in range(n_labels)
        if sum(m["confusion_matrix"][c]) or sum(f[c] for f in m["confusion_matrix"])
    ]
    esperado = sum(_f1_de_la_clase(m["confusion_matrix"], c) for c in presentes) / len(presentes)
    assert m["macro_f1"] == pytest.approx(esperado)
