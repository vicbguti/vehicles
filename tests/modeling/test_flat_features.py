"""Aplanado a ancho fijo: esquema, relleno canónico y alineación de filas.

`build_flat_arrays` hace relleno, `reshape`, `broadcast_to` y avance de cursor
sobre episodios de distinto tamaño. Un desfase ahí no lanza ninguna excepción:
produce un modelo entrenado contra las etiquetas del episodio equivocado. Estas
pruebas fijan justamente eso.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.features import (
    CONTEXT_BLOCK,
    TRUCK_BLOCK,
    VEHICLE_BLOCK,
    BlockScaler,
    build_episode_tensors,
    feature_names,
)
from src.modeling.flat_features import build_flat_arrays, flat_feature_names

CLASSES = ["AUTOMOVIL", "CAMIONETA", "JEEP", "MOTOCICLETA"]


def _rows(episode_id: str, specs: list[tuple[str, str, float, str]], caps: list[float]):
    """specs = [(uid, clase, cu, truck), ...]"""
    return pd.DataFrame(
        [
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
                "n_loaded": sum(1 for s in specs if s[3] != "SIN_CAMION"),
                "cu_utilized": sum(s[2] for s in specs if s[3] != "SIN_CAMION"),
            }
            for uid, clase, cu, truck in specs
        ]
    )


def _episodio(episode_id: str, specs, caps):
    return build_episode_tensors(_rows(episode_id, specs, caps), CLASSES)


def _scaler(episodios):
    return BlockScaler.fit(episodios, CLASSES)


# --------------------------------------------------------------------- esquema
def test_el_ancho_es_vehiculo_mas_contexto_mas_camiones_rellenados():
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0, 3.0])
    flat = build_flat_arrays([ep], _scaler([ep]), max_trucks=4)

    nombres = feature_names(CLASSES)
    esperado = (
        len(nombres[VEHICLE_BLOCK]) + len(nombres[CONTEXT_BLOCK]) + 4 * len(nombres[TRUCK_BLOCK])
    )
    assert flat.n_features == esperado
    assert flat.X.dtype == np.float32


def test_los_nombres_de_columna_coinciden_con_el_ancho_real():
    # Si `flat_feature_names` y `build_flat_arrays` se desincronizan, el
    # feature_schema.json publicado etiquetaría mal cada columna.
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0])
    flat = build_flat_arrays([ep], _scaler([ep]), max_trucks=3)
    assert len(flat_feature_names(CLASSES, max_trucks=3)) == flat.n_features


def test_los_nombres_de_camion_van_por_posicion_canonica():
    nombres = flat_feature_names(CLASSES, max_trucks=2)
    de_camion = [n for n in nombres if n.startswith("camion_")]
    assert all(n.startswith("camion_1_") for n in de_camion[: len(de_camion) // 2])
    assert all(n.startswith("camion_2_") for n in de_camion[len(de_camion) // 2 :])


# --------------------------------------------------------------------- relleno
def test_la_cola_del_bloque_de_camiones_queda_en_cero():
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0])  # 1 camión
    flat = build_flat_arrays([ep], _scaler([ep]), max_trucks=4)

    truck_dim = ep.truck.shape[1]
    inicio_camiones = flat.n_features - 4 * truck_dim
    relleno = flat.X[0, inicio_camiones + truck_dim :]
    assert np.array_equal(relleno, np.zeros_like(relleno))


def test_los_camiones_reales_van_en_orden_canonico_descendente():
    # El camión de mayor capacidad ocupa la posición 1, no el orden del parquet.
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_2")], [3.0, 9.0])
    assert ep.capacities.tolist() == [9.0, 3.0]

    scaler = _scaler([ep])
    flat = build_flat_arrays([ep], scaler, max_trucks=4)

    truck_dim = ep.truck.shape[1]
    inicio = flat.n_features - 4 * truck_dim
    escalado = scaler.transform(TRUCK_BLOCK, ep.truck)
    assert np.allclose(flat.X[0, inicio : inicio + 2 * truck_dim], escalado.reshape(-1), atol=1e-5)


def test_una_flota_mayor_que_el_relleno_falla_ruidosamente():
    # El contrato que el módulo promete: no generaliza por encima de max_trucks,
    # y lo dice en vez de truncar en silencio.
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0, 5.0, 4.0])
    with pytest.raises(ValueError, match="camiones"):
        build_flat_arrays([ep], _scaler([ep]), max_trucks=2)


# ------------------------------------------------------------------ alineación
def test_el_cursor_no_se_desfasa_entre_episodios_de_distinto_tamano():
    e1 = _episodio(
        "E1",
        [("a", "AUTOMOVIL", 1.0, "CAMION_1"), ("b", "JEEP", 1.2, "SIN_CAMION")],
        [6.0],
    )
    e2 = _episodio("E2", [("c", "MOTOCICLETA", 0.2, "CAMION_1")], [4.0, 2.0])
    e3 = _episodio(
        "E3",
        [
            ("d", "AUTOMOVIL", 1.0, "CAMION_2"),
            ("e", "CAMIONETA", 1.5, "CAMION_1"),
            ("f", "JEEP", 1.2, "SIN_CAMION"),
        ],
        [7.0, 5.0],
    )
    episodios = [e1, e2, e3]
    flat = build_flat_arrays(episodios, _scaler(episodios), max_trucks=4)

    assert flat.n_rows == 2 + 1 + 3
    assert flat.episode_index.tolist() == [0, 0, 1, 2, 2, 2]
    assert flat.episode_ids == ["E1", "E2", "E3"]
    # El target de cada tramo es el del episodio que le corresponde.
    esperado = np.concatenate([e.target for e in episodios])
    assert np.array_equal(flat.target, esperado)


def test_cada_fila_de_un_episodio_comparte_contexto_y_flota():
    ep = _episodio(
        "E1",
        [("a", "AUTOMOVIL", 1.0, "CAMION_1"), ("b", "JEEP", 1.2, "SIN_CAMION")],
        [6.0, 3.0],
    )
    flat = build_flat_arrays([ep], _scaler([ep]), max_trucks=4)

    vehicle_dim = ep.vehicle.shape[1]
    # Todo lo que va después del bloque del vehículo es del episodio, no de la fila.
    assert np.array_equal(flat.X[0, vehicle_dim:], flat.X[1, vehicle_dim:])
    # Y el bloque del vehículo sí distingue las dos filas.
    assert not np.array_equal(flat.X[0, :vehicle_dim], flat.X[1, :vehicle_dim])


def test_el_escalado_se_aplica_por_bloque():
    ep = _episodio("E1", [("a", "AUTOMOVIL", 1.0, "CAMION_1")], [6.0, 3.0])
    scaler = _scaler([ep])
    flat = build_flat_arrays([ep], scaler, max_trucks=4)

    vehicle_dim = ep.vehicle.shape[1]
    context_dim = len(ep.context)
    esperado_vehiculo = scaler.transform(VEHICLE_BLOCK, ep.vehicle)[0]
    esperado_contexto = scaler.transform(CONTEXT_BLOCK, ep.context[None, :])[0]

    assert np.allclose(flat.X[0, :vehicle_dim], esperado_vehiculo, atol=1e-5)
    assert np.allclose(
        flat.X[0, vehicle_dim : vehicle_dim + context_dim], esperado_contexto, atol=1e-5
    )


def test_sin_episodios_falla():
    with pytest.raises(ValueError):
        build_flat_arrays([], BlockScaler(), max_trucks=4)
