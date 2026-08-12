"""Pruebas del maestro exacto (`src/loading/labeler.py`).

Este módulo es la verdad de referencia de todo el proyecto: cada métrica
publicada es condicional a que `assign_vehicles` sea correcto, y hasta ahora no
tenía ni una prueba.

La estrategia es de tres capas:

1. **Invariantes** que deben cumplirse en cualquier instancia (factibilidad,
   conservación de vehículos).
2. **Oráculo por fuerza bruta** para instancias diminutas, donde enumerar todo
   el espacio de asignaciones es barato y obviamente correcto. Es lo que
   verifica de verdad la optimalidad del DP.
3. **Propiedades metamórficas**: relaciones que deben mantenerse entre entradas
   emparentadas (escalado, permutación, monotonía). Cubren clases de error que
   un oráculo sobre casos pequeños no alcanza a ver.

Las instancias aleatorias usan semilla fija: reproducibles, sin dependencias
nuevas.
"""

from __future__ import annotations

import itertools
import random
from fractions import Fraction

import pytest

from src.loading.labeler import LabelResult, Vehicle, assign_vehicles

DEFERRED = "SIN_CAMION"

# CU por clase tal como los usa el proyecto (config/vehicle_classes.yaml).
# Se incluye Fraction(2, 3) a propósito: el docstring del módulo documenta que
# una escala decimal fija corrompe las fracciones periódicas, y ese fue un bug
# real durante el desarrollo.
CU_POR_CLASE = {
    "MOTOCICLETA": Fraction(1, 3),
    "AUTOMOVIL": Fraction(1),
    "CAMIONETA": Fraction(3, 2),
    "JEEP": Fraction(2, 3),
}


# --------------------------------------------------------------------------- utilidades


def _vehiculos(spec: dict[str, int]) -> list[Vehicle]:
    """Construye vehículos a partir de {clase: cantidad}, con uid determinista."""
    out: list[Vehicle] = []
    for clase in sorted(spec):
        for i in range(spec[clase]):
            out.append(Vehicle(uid=f"{clase}-{i:03d}", clase=clase, cu=CU_POR_CLASE[clase]))
    return out


def _carga_por_camion(res: LabelResult, vehiculos: list[Vehicle], n_trucks: int) -> list[Fraction]:
    """CU real acumulado por camión, recomputado desde la asignación."""
    cu = {v.uid: Fraction(v.cu) for v in vehiculos}
    cargas = [Fraction(0)] * n_trucks
    for uid, destino in res.assignment.items():
        if destino != DEFERRED:
            cargas[int(destino.split("_")[1]) - 1] += cu[uid]
    return cargas


def _oraculo_fuerza_bruta(
    vehiculos: list[Vehicle], capacidades: list[Fraction]
) -> tuple[int, Fraction]:
    """(n_loaded, cu_utilized) óptimos por enumeración exhaustiva.

    Obviamente correcto y obviamente lento: solo usable con muy pocos
    vehículos. El objetivo es léxico — primero cuántos vehículos se cargan,
    después cuánto CU se aprovecha.
    """
    n_trucks = len(capacidades)
    mejor = (0, Fraction(0))
    # -1 = diferido; 0..T-1 = índice de camión
    for combo in itertools.product(range(-1, n_trucks), repeat=len(vehiculos)):
        cargas = [Fraction(0)] * n_trucks
        n_cargados = 0
        for v, destino in zip(vehiculos, combo, strict=True):
            if destino >= 0:
                cargas[destino] += Fraction(v.cu)
                n_cargados += 1
        if any(c > cap for c, cap in zip(cargas, capacidades, strict=True)):
            continue
        candidato = (n_cargados, sum(cargas))
        if candidato > mejor:
            mejor = candidato
    return mejor


def _instancias_aleatorias(n: int, seed: int, max_veh: int = 6, max_trucks: int = 3):
    """Genera `n` instancias pequeñas y reproducibles."""
    rng = random.Random(seed)
    clases = sorted(CU_POR_CLASE)
    for _ in range(n):
        n_veh = rng.randint(1, max_veh)
        vehiculos = [
            Vehicle(uid=f"v{i:03d}", clase=(c := rng.choice(clases)), cu=CU_POR_CLASE[c])
            for i in range(n_veh)
        ]
        n_trucks = rng.randint(1, max_trucks)
        capacidades = [Fraction(rng.randint(1, 6)) for _ in range(n_trucks)]
        yield vehiculos, capacidades


# --------------------------------------------------------------------------- invariantes


@pytest.mark.parametrize("caso", range(60))
def test_el_plan_nunca_excede_la_capacidad(caso: int) -> None:
    """Invariante duro: ningún camión puede sobrepasar su capacidad."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=1000 + caso)))
    res = assign_vehicles(vehiculos, capacidades)
    cargas = _carga_por_camion(res, vehiculos, len(capacidades))
    for carga, cap in zip(cargas, capacidades, strict=True):
        assert carga <= cap, f"camión sobrecargado: {carga} > {cap}"


@pytest.mark.parametrize("caso", range(60))
def test_todo_vehiculo_recibe_exactamente_un_destino(caso: int) -> None:
    """Ni se pierden vehículos ni se duplican: cargados + diferidos == total."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=2000 + caso)))
    res = assign_vehicles(vehiculos, capacidades)

    assert set(res.assignment) == {v.uid for v in vehiculos}
    n_diferidos = sum(1 for d in res.assignment.values() if d == DEFERRED)
    n_cargados = len(vehiculos) - n_diferidos
    assert res.n_loaded == n_cargados
    assert res.n_deferred == n_diferidos
    assert res.n_loaded + res.n_deferred == len(vehiculos)


@pytest.mark.parametrize("caso", range(60))
def test_las_metricas_reportadas_coinciden_con_la_asignacion(caso: int) -> None:
    """`cu_utilized` y `truck_loads` deben derivarse del plan, no divergir."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=3000 + caso)))
    res = assign_vehicles(vehiculos, capacidades)

    cargas = _carga_por_camion(res, vehiculos, len(capacidades))
    assert res.cu_utilized == pytest.approx(float(sum(cargas)))
    for reportada, real in zip(res.truck_loads, cargas, strict=True):
        assert reportada == pytest.approx(float(real))


# --------------------------------------------------------------------- oráculo exhaustivo


@pytest.mark.parametrize("caso", range(40))
def test_iguala_al_optimo_de_fuerza_bruta(caso: int) -> None:
    """El DP debe alcanzar exactamente el óptimo léxico de un oráculo tonto."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=4000 + caso, max_veh=5)))
    res = assign_vehicles(vehiculos, capacidades)
    esperado = _oraculo_fuerza_bruta(vehiculos, capacidades)

    assert res.optimal is True
    assert (res.n_loaded, Fraction(res.cu_utilized).limit_denominator(1000)) == esperado


def test_prioriza_cargar_mas_vehiculos_antes_que_llenar_mas() -> None:
    """El objetivo es léxico: 3 vehículos pequeños ganan a 1 grande que llena más.

    Un camión de 3 CU con una CAMIONETA (1.5) y tres MOTOCICLETAS (1/3 c/u).
    Cargar los cuatro no cabe (1.5 + 1 = 2.5 <= 3 sí cabe), así que se fuerza
    el conflicto con una capacidad justa de 1.5.
    """
    vehiculos = _vehiculos({"CAMIONETA": 1, "MOTOCICLETA": 3})
    res = assign_vehicles(vehiculos, [Fraction(3, 2)])

    # Con 1.5 de capacidad: o la camioneta (1 vehículo, 1.5 CU) o las tres
    # motos (3 vehículos, 1.0 CU). Gana el conteo.
    assert res.n_loaded == 3
    assert res.assignment["CAMIONETA-000"] == DEFERRED


# ----------------------------------------------------------------- propiedades metamórficas


@pytest.mark.parametrize("factor", [2, 3, 10])
def test_invariancia_de_escala(factor: int) -> None:
    """Multiplicar CU y capacidades por k no puede cambiar el plan.

    Esto ejercita el escalado exacto por fracciones. Con una escala decimal
    fija, valores como 1/3 se corrompen y el plan cambia.
    """
    base = _vehiculos({"MOTOCICLETA": 4, "JEEP": 2, "AUTOMOVIL": 2})
    caps = [Fraction(7, 2), Fraction(2)]

    escalados = [Vehicle(uid=v.uid, clase=v.clase, cu=Fraction(v.cu) * factor) for v in base]
    caps_escaladas = [c * factor for c in caps]

    r1 = assign_vehicles(base, caps)
    r2 = assign_vehicles(escalados, caps_escaladas)

    assert r1.assignment == r2.assignment
    assert r1.n_loaded == r2.n_loaded
    assert r2.cu_utilized == pytest.approx(r1.cu_utilized * factor)


@pytest.mark.parametrize("caso", range(30))
def test_el_objetivo_no_depende_del_orden_de_los_vehiculos(caso: int) -> None:
    """Permutar la entrada puede cambiar QUÉ vehículo va dónde, pero nunca el
    valor objetivo alcanzado."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=5000 + caso)))
    barajados = list(vehiculos)
    random.Random(caso).shuffle(barajados)

    r1 = assign_vehicles(vehiculos, capacidades)
    r2 = assign_vehicles(barajados, capacidades)

    assert (r1.n_loaded, round(r1.cu_utilized, 9)) == (r2.n_loaded, round(r2.cu_utilized, 9))


@pytest.mark.parametrize("caso", range(30))
def test_mas_capacidad_nunca_carga_menos(caso: int) -> None:
    """Monotonía: ampliar un camión no puede empeorar el óptimo."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=6000 + caso)))
    ampliadas = [c + 2 for c in capacidades]

    base = assign_vehicles(vehiculos, capacidades)
    mayor = assign_vehicles(vehiculos, ampliadas)

    assert mayor.n_loaded >= base.n_loaded


@pytest.mark.parametrize("caso", range(30))
def test_agregar_un_camion_nunca_carga_menos(caso: int) -> None:
    """Monotonía en el eje de flota: un camión extra no puede empeorar nada."""
    vehiculos, capacidades = next(iter(_instancias_aleatorias(1, seed=7000 + caso)))

    base = assign_vehicles(vehiculos, capacidades)
    con_extra = assign_vehicles(vehiculos, [*capacidades, Fraction(3)])

    assert con_extra.n_loaded >= base.n_loaded


def test_el_orden_de_la_flota_no_cambia_el_valor_objetivo() -> None:
    """Permutar las capacidades no cambia cuánto se puede cargar.

    Es la propiedad que sostiene la canonicalización por capacidad: si el
    objetivo dependiera del orden de la flota, ordenarla antes de etiquetar
    cambiaría las etiquetas de forma no aprendible.
    """
    vehiculos = _vehiculos({"AUTOMOVIL": 3, "CAMIONETA": 2, "MOTOCICLETA": 3})
    caps = [Fraction(1), Fraction(4), Fraction(5, 2)]

    valores = set()
    for perm in itertools.permutations(caps):
        r = assign_vehicles(vehiculos, list(perm))
        valores.add((r.n_loaded, round(r.cu_utilized, 9)))

    assert len(valores) == 1, f"el objetivo depende del orden de la flota: {valores}"


# --------------------------------------------------------------------- determinismo y bordes


def test_es_determinista_sin_semilla() -> None:
    vehiculos = _vehiculos({"AUTOMOVIL": 4, "MOTOCICLETA": 3})
    caps = [Fraction(3), Fraction(2)]
    primero = assign_vehicles(vehiculos, caps)
    segundo = assign_vehicles(vehiculos, caps)
    assert primero.assignment == segundo.assignment


def test_la_misma_semilla_da_el_mismo_plan() -> None:
    vehiculos = _vehiculos({"AUTOMOVIL": 5, "MOTOCICLETA": 4})
    caps = [Fraction(3)]
    a = assign_vehicles(vehiculos, caps, seed=123)
    b = assign_vehicles(vehiculos, caps, seed=123)
    assert a.assignment == b.assignment


def test_la_semilla_solo_cambia_a_quien_se_carga_no_cuanto() -> None:
    """La semilla desempata entre vehículos intercambiables de la misma clase;
    el valor objetivo no puede moverse."""
    vehiculos = _vehiculos({"AUTOMOVIL": 6})
    caps = [Fraction(3)]
    resultados = [assign_vehicles(vehiculos, caps, seed=s) for s in range(8)]

    assert len({r.n_loaded for r in resultados}) == 1
    assert len({round(r.cu_utilized, 9) for r in resultados}) == 1


def test_sin_vehiculos() -> None:
    res = assign_vehicles([], [Fraction(5)])
    assert res.n_loaded == 0
    assert res.assignment == {}
    assert res.optimal is True


def test_sin_camiones_todo_se_difiere() -> None:
    vehiculos = _vehiculos({"AUTOMOVIL": 3})
    res = assign_vehicles(vehiculos, [])
    assert res.n_loaded == 0
    assert res.n_deferred == 3
    assert set(res.assignment.values()) == {DEFERRED}
    assert res.optimal is True


def test_nada_cabe() -> None:
    """Capacidad menor que el vehículo más pequeño: todo diferido, sin fallar."""
    vehiculos = _vehiculos({"CAMIONETA": 2})
    res = assign_vehicles(vehiculos, [Fraction(1, 4)])
    assert res.n_loaded == 0
    assert res.cu_utilized == pytest.approx(0.0)


def test_ajuste_exacto() -> None:
    """Tres AUTOMOVIL (1 CU) en un camión de exactamente 3 CU: entran los tres."""
    vehiculos = _vehiculos({"AUTOMOVIL": 3})
    res = assign_vehicles(vehiculos, [Fraction(3)])
    assert res.n_loaded == 3
    assert res.cu_utilized == pytest.approx(3.0)
    assert DEFERRED not in res.assignment.values()


def test_fracciones_periodicas_son_exactas() -> None:
    """Doce vehículos de 2/3 CU caben exactos en 8 CU.

    Con una escala decimal fija (x10), 2/3 -> 7 y 12*7 = 84 > 80: el labeler
    concluiría que uno no cabe. Es el bug que documenta el módulo.
    """
    vehiculos = [Vehicle(uid=f"j{i:02d}", clase="JEEP", cu=Fraction(2, 3)) for i in range(12)]
    res = assign_vehicles(vehiculos, [Fraction(8)])

    assert res.n_loaded == 12
    assert res.cu_utilized == pytest.approx(8.0)


def test_fracciones_periodicas_son_exactas_tambien_llegando_como_float() -> None:
    """El mismo caso, pero con `cu` en float — que es como llega de verdad.

    Importa distinguirlo: `_as_fraction` devuelve tal cual los Fraction, así
    que una prueba que solo use Fraction NO ejercita el `limit_denominator`, y
    una regresión a escala decimal fija pasaría desapercibida. Los datos reales
    vienen de config/vehicle_classes.yaml como float.

    Tres vehículos de 1/3 CU en un camión de 1 CU: con fracciones exactas
    entran los tres; con escala x10 cada uno pesa 0.3, suman 0.9 y el CU
    reportado sería incorrecto.
    """
    un_tercio = 1.0 / 3.0
    vehiculos = [Vehicle(uid=f"m{i:02d}", clase="MOTOCICLETA", cu=un_tercio) for i in range(3)]
    res = assign_vehicles(vehiculos, [1.0])

    assert res.n_loaded == 3
    assert res.cu_utilized == pytest.approx(1.0)
    assert DEFERRED not in res.assignment.values()


def test_el_presupuesto_agotado_marca_optimal_false_pero_deja_un_plan_factible() -> None:
    """Si se acaba el tiempo, el plan devuelto debe seguir respetando capacidad.

    Es el único camino donde un bug produciría etiquetas silenciosamente malas:
    downstream confía en `optimal` para filtrar.
    """
    vehiculos = [
        Vehicle(uid=f"v{i:03d}", clase=c, cu=CU_POR_CLASE[c])
        for i, c in enumerate(sorted(CU_POR_CLASE) * 15)
    ]
    capacidades = [Fraction(5)] * 6
    res = assign_vehicles(vehiculos, capacidades, time_budget_s=0.001)

    cargas = _carga_por_camion(res, vehiculos, len(capacidades))
    for carga, cap in zip(cargas, capacidades, strict=True):
        assert carga <= cap
    assert res.n_loaded + res.n_deferred == len(vehiculos)
