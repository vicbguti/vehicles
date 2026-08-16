"""Decoder de capacidad y las tres garantías que el plan de salida debe cumplir.

El decodificador promete tres cosas, y las tres se afirman por escrito en el
reporte, así que las tres tienen que estar fijadas aquí:

- **Capacidad.** Ningún camión excede su espacio. Es la invariante dura.
- **Unicidad y totalidad.** Cada vehículo termina en exactamente un camión o
  diferido: ninguno queda sin resolver, ninguno recibe dos destinos.
- **Identidad.** El índice del arreglo *es* el vehículo; ninguno se duplica ni
  se pierde.

Las dos últimas se sostienen sobre un detalle fácil de romper sin querer: que
`_vehicle_order` devuelva una **permutación** de los índices. Un `sorted` sobre
un subconjunto, o un filtro, seguirían pasando todas las pruebas por caso
concreto y dejarían el reporte afirmando algo falso. De ahí el barrido aleatorio
y la prueba explícita de permutación.

Las instancias aleatorias usan semilla fija: reproducibles, sin dependencias
nuevas.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.modeling.capacity_decoder import (
    DEFERRED,
    POLICIES,
    _vehicle_order,
    decode_episode,
    greedy_first_fit_decreasing,
    split_logits,
)

# Los CU reales de config/vehicle_classes.yaml, más 2/3: no es representable en
# decimal y es justo donde un decoder con la comparación mal puesta se rompe.
_CU_POSIBLES = (0.2, 1.0, 1.1, 1.4, 2 / 3)

# Cuántos episodios recorre cada barrido. Suficiente para cruzar flota vacía,
# manifiesto vacío, capacidad de sobra y capacidad escasa en la misma prueba.
_CASOS = 200


def _logits(preferences: list[list[float]], defer: list[float]) -> np.ndarray:
    """Arma (V, 1+T) con el diferimiento en la columna 0."""
    return np.column_stack([np.array(defer, dtype=float), np.array(preferences, dtype=float)])


def _episodio_aleatorio(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Un episodio cualquiera dentro del dominio del decoder: `(logits, cu, capacities)`.

    Incluye a propósito los bordes -- cero vehículos, cero camiones -- y alterna
    flotas holgadas con flotas escasas, porque la coherencia entre el plan y las
    cargas sólo es informativa cuando de verdad hay vehículos que no caben.
    """
    n_vehicles = int(rng.integers(0, 13))
    n_trucks = int(rng.integers(0, 5))
    cu = rng.choice(_CU_POSIBLES, size=n_vehicles)

    # Holgada: entra casi todo. Escasa: hay que dejar vehículos fuera.
    holgada = bool(rng.integers(0, 2))
    total = cu.sum() if n_vehicles else 1.0
    escala = (2.0 if holgada else 0.35) * total / max(n_trucks, 1)
    capacities = np.round(rng.uniform(0.5 * escala, 1.5 * escala, size=n_trucks), 2)

    # scale=5 hace que las preferencias sean fuertes y se contradigan entre sí:
    # el modelo "insiste" en camiones que ya están llenos, que es el caso duro.
    logits = rng.normal(scale=5.0, size=(n_vehicles, n_trucks + 1))
    return logits, cu, capacities


def _verificar_particion(decoded, cu: np.ndarray, n_trucks: int, pista: str) -> None:
    """Las tres garantías del plan, sobre un episodio ya decodificado."""
    assignment = decoded.assignment

    # Totalidad: hay una decisión por vehículo, ni una más ni una menos.
    assert len(assignment) == len(cu), pista
    assert decoded.n_loaded + decoded.n_deferred == len(cu), pista

    # Dominio: todo destino es un camión que existe, o el diferimiento.
    assert set(assignment.tolist()) <= {DEFERRED, *range(n_trucks)}, pista

    # Coherencia entre el plan publicado y las cargas reportadas. `truck_loads`
    # se calcula como `capacities - remaining`, sin mirar `assignment`: si las
    # dos mitades se separaran, esto es lo único que se daría cuenta.
    for j in range(n_trucks):
        esperado = cu[assignment == j].sum()
        assert decoded.truck_loads[j] == pytest.approx(esperado), f"{pista}, camión {j}"

    # Conservación: nada se carga sin salir del manifiesto.
    assert decoded.cu_loaded == pytest.approx(cu[assignment != DEFERRED].sum()), pista

    assert decoded.is_feasible, pista


@pytest.mark.parametrize("policy", POLICIES)
def test_nunca_excede_la_capacidad_aunque_el_modelo_insista(policy):
    """Tres vehículos de 3.0 CU, un camión de 6.0, y el modelo quiere meterlos
    todos ahí. Sólo pueden entrar dos."""
    logits = _logits([[9.0], [9.0], [9.0]], defer=[-9.0, -9.0, -9.0])
    decoded = decode_episode(logits, cu=[3.0, 3.0, 3.0], capacities=[6.0], policy=policy)

    assert decoded.is_feasible
    assert decoded.max_overflow == 0.0
    assert decoded.n_loaded == 2
    assert decoded.n_deferred == 1


@pytest.mark.parametrize("policy", POLICIES)
def test_flota_vacia_difiere_todo(policy):
    logits = np.array([[1.0], [1.0]])
    decoded = decode_episode(logits, cu=[1.0, 1.0], capacities=[], policy=policy)
    assert decoded.n_loaded == 0
    assert decoded.assignment.tolist() == [DEFERRED, DEFERRED]


@pytest.mark.parametrize("policy", POLICIES)
def test_manifiesto_vacio(policy):
    decoded = decode_episode(np.zeros((0, 2)), cu=[], capacities=[6.0], policy=policy)
    assert decoded.n_loaded == 0
    assert decoded.is_feasible


def test_un_solo_camion_con_capacidad_de_sobra():
    logits = _logits([[5.0], [5.0]], defer=[0.0, 0.0])
    decoded = decode_episode(logits, cu=[1.0, 1.4], capacities=[6.0])
    assert decoded.n_loaded == 2
    assert decoded.cu_loaded == pytest.approx(2.4)


def test_carga_exacta_hasta_el_ultimo_cu():
    """2/3 CU x 9 = 6.0 exacto. El decoder no puede fallar por un epsilon."""
    cu = [2 / 3] * 9
    logits = _logits([[1.0]] * 9, defer=[0.0] * 9)
    decoded = decode_episode(logits, cu=cu, capacities=[6.0])

    assert decoded.n_loaded == 9
    assert decoded.is_feasible
    assert decoded.cu_loaded == pytest.approx(6.0)


def test_capacidad_insuficiente_para_cualquier_vehiculo():
    logits = _logits([[5.0], [5.0]], defer=[0.0, 0.0])
    decoded = decode_episode(logits, cu=[4.0, 4.0], capacities=[3.0])
    assert decoded.n_loaded == 0
    assert decoded.n_deferred == 2


def test_cuatro_camiones_respeta_la_preferencia_del_modelo():
    # El modelo prefiere el camión 2 (índice 2) para el único vehículo.
    logits = _logits([[0.1, 0.2, 9.0, 0.3]], defer=[-5.0])
    decoded = decode_episode(logits, cu=[1.0], capacities=[6.0, 6.0, 6.0, 6.0])
    assert decoded.assignment.tolist() == [2]


def test_cae_al_siguiente_camion_cuando_el_preferido_esta_lleno():
    logits = _logits([[9.0, 1.0], [9.0, 1.0]], defer=[-5.0, -5.0])
    decoded = decode_episode(logits, cu=[4.0, 4.0], capacities=[6.0, 6.0])
    assert sorted(decoded.assignment.tolist()) == [0, 1]


def test_capacidades_iguales_no_rompen_la_factibilidad():
    logits = _logits([[1.0, 1.0]] * 6, defer=[0.0] * 6)
    decoded = decode_episode(logits, cu=[2.0] * 6, capacities=[6.0, 6.0])
    assert decoded.is_feasible
    assert decoded.n_loaded == 6


def test_la_politica_de_conteo_carga_al_menos_tanto_como_la_del_modelo():
    """Con capacidad escasa, atender primero a los vehículos pequeños maximiza
    el conteo, que es el objetivo primario del maestro."""
    cu = [5.0, 1.0, 1.0, 1.0]
    # El modelo prefiere fuertemente cargar el grande primero.
    logits = _logits([[9.0], [1.0], [1.0], [1.0]], defer=[-1.0, -1.0, -1.0, -1.0])

    por_modelo = decode_episode(logits, cu, capacities=[6.0], policy="model")
    por_conteo = decode_episode(logits, cu, capacities=[6.0], policy="count")

    assert por_modelo.n_loaded == 2  # 5.0 + 1.0
    assert por_conteo.n_loaded == 3  # 1.0 + 1.0 + 1.0
    assert por_conteo.n_loaded >= por_modelo.n_loaded


def test_respect_defer_honra_el_sin_camion_predicho():
    # El vehículo 1 tiene margen negativo: el modelo prefiere diferirlo.
    logits = _logits([[1.0], [-5.0]], defer=[0.0, 5.0])
    respetando = decode_episode(logits, cu=[1.0, 1.0], capacities=[6.0], policy="respect_defer")
    ignorando = decode_episode(logits, cu=[1.0, 1.0], capacities=[6.0], policy="count")

    assert respetando.n_loaded == 1
    assert ignorando.n_loaded == 2  # cabía perfectamente


def test_la_utilizacion_se_calcula_sobre_la_capacidad_total():
    logits = _logits([[5.0, 1.0]], defer=[0.0])
    decoded = decode_episode(logits, cu=[3.0], capacities=[6.0, 4.0])
    assert decoded.utilization == pytest.approx(3.0 / 10.0)


def test_split_logits_separa_diferir_de_los_camiones():
    logits = np.array([[0.5, 1.0, 2.0, 3.0]])
    pares, diferir = split_logits(logits, n_trucks=3)
    assert diferir.tolist() == [0.5]
    assert pares.tolist() == [[1.0, 2.0, 3.0]]


def test_split_logits_falla_si_faltan_columnas():
    with pytest.raises(ValueError, match="al menos"):
        split_logits(np.zeros((2, 3)), n_trucks=4)


def test_el_greedy_de_referencia_tambien_es_factible():
    decoded = greedy_first_fit_decreasing(cu=[4.0, 3.0, 2.0, 1.0], capacities=[6.0, 6.0])
    assert decoded.is_feasible
    assert decoded.n_loaded == 4


def test_el_greedy_puede_ser_peor_que_el_optimo():
    """El caso del reporte: llenar con el más grande primero desperdicia espacio."""
    decoded = greedy_first_fit_decreasing(cu=[4.0, 4.0, 3.0, 3.0], capacities=[6.0, 6.0])
    assert decoded.n_loaded == 2  # 4+4 en camiones distintos, los 3.0 no caben
    assert decoded.is_feasible


def test_politica_desconocida_falla():
    with pytest.raises(ValueError, match="Política desconocida"):
        decode_episode(np.zeros((1, 2)), cu=[1.0], capacities=[6.0], policy="magia")


@pytest.mark.parametrize("policy", POLICIES)
def test_el_plan_es_una_particion_total_del_manifiesto(policy):
    """Sobre episodios aleatorios: totalidad, dominio válido y coherencia entre
    el plan y las cargas. Es la garantía que el reporte afirma por escrito."""
    for caso in range(_CASOS):
        rng = np.random.default_rng(20260815 + caso)
        logits, cu, capacities = _episodio_aleatorio(rng)
        decoded = decode_episode(logits, cu, capacities, policy=policy)
        _verificar_particion(decoded, cu, len(capacities), f"política {policy}, caso {caso}")


@pytest.mark.parametrize("policy", POLICIES)
def test_el_orden_de_vehiculos_es_una_permutacion(policy):
    """La propiedad de la que cuelgan la unicidad y la totalidad.

    Si `_vehicle_order` dejara de recorrer todos los vehículos exactamente una
    vez -- un filtro, un `sorted` sobre un subconjunto -- el decoder seguiría
    devolviendo planes factibles, sólo que incompletos, y ninguna prueba por caso
    concreto lo notaría.
    """
    for caso in range(_CASOS):
        rng = np.random.default_rng(90000 + caso)
        n_vehicles = int(rng.integers(0, 13))
        cu = rng.choice(_CU_POSIBLES, size=n_vehicles)
        margin = rng.normal(scale=5.0, size=n_vehicles)

        orden = _vehicle_order(policy, cu, margin)

        assert sorted(orden.tolist()) == list(range(n_vehicles)), f"política {policy}, caso {caso}"


def test_el_greedy_tambien_produce_una_particion_total():
    """La línea base construye su `DecodedEpisode` por la misma vía y comparte
    el mismo punto ciego, así que responde por la misma invariante."""
    for caso in range(_CASOS):
        rng = np.random.default_rng(70000 + caso)
        _, cu, capacities = _episodio_aleatorio(rng)
        decoded = greedy_first_fit_decreasing(cu, capacities)
        _verificar_particion(decoded, cu, len(capacities), f"caso {caso}")
