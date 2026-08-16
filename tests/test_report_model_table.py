"""Las dos puertas de comparabilidad de la tabla comparativa.

La tabla publicó dos errores del mismo tipo con dos años de diferencia: primero
filas medidas con particiones distintas, después filas medidas con **métricas**
distintas bajo el mismo encabezado. Los dos sobrevivieron meses porque las
cifras equivocadas eran plausibles.

Ninguna de las dos puertas se puede comprobar mirando la tabla: hay que
comprobar que **rechazan** lo que deben rechazar. Eso es lo que hay aquí.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# `scripts/` no es un paquete importable (no tiene __init__.py y el repo no se
# instala como distribución), así que se carga por ruta. Es el mismo patrón que
# usan los propios scripts para resolver `src.*`.
_spec = importlib.util.spec_from_file_location(
    "report_model_table", REPO / "scripts" / "report_model_table.py"
)
rmt = importlib.util.module_from_spec(_spec)
sys.modules["report_model_table"] = rmt
_spec.loader.exec_module(rmt)


def _agregados_completos(**overrides) -> dict:
    """Una fila válida: exactamente lo que emite `metrics.aggregate()`."""
    base = dict.fromkeys(rmt.METRICAS_PUBLICADAS, 0.5)
    return {**base, **overrides}


# --- puerta 1: la partición -----------------------------------------------


def test_una_fuente_sin_particion_declarada_no_entra():
    """El caso real: los tres JSON de Kedro no traían `split_strategy`, así que
    la puerta que existía para vigilarlos no llegaba a mirarlos."""
    with pytest.raises(SystemExit, match="split_strategy=None"):
        rmt._exigir_protocolo_temporal({}, "sin_clave.json")


def test_una_fuente_con_otra_particion_no_entra():
    with pytest.raises(SystemExit, match="split_strategy='hash'"):
        rmt._exigir_protocolo_temporal({"split_strategy": "hash"}, "hash.json")


def test_la_particion_temporal_pasa():
    rmt._exigir_protocolo_temporal({"split_strategy": "time"}, "ok.json")


# --- puerta 2: la métrica --------------------------------------------------


def test_una_fila_a_la_que_le_falta_una_metrica_no_se_publica():
    """La regresión de R9: antes `.get()` devolvía None --o la métrica de al
    lado-- y la fila se publicaba igual con otra cosa en la columna."""
    incompletos = _agregados_completos()
    del incompletos["f1_defer"]

    with pytest.raises(SystemExit, match="f1_defer"):
        rmt._fila("Modelo X", incompletos)


def test_el_mensaje_dice_que_esa_fila_se_midio_de_otra_forma():
    """Un «falta una clave» invita a rellenarla; el punto es que la fila no es
    comparable, y el mensaje tiene que decir eso."""
    faltantes = _agregados_completos()
    del faltantes["macro_f1"]

    with pytest.raises(SystemExit, match="no es comparable"):
        rmt._fila("Modelo X", faltantes)


def test_las_metricas_publicadas_incluyen_las_dos_f1_por_separado():
    """Que estén las dos es la corrección; que estén separadas es el punto."""
    assert "f1_defer" in rmt.METRICAS_PUBLICADAS
    assert "macro_f1" in rmt.METRICAS_PUBLICADAS


def test_una_fila_completa_se_publica_con_las_dos_f1_en_columnas_distintas():
    fila = rmt._fila("Modelo X", _agregados_completos(f1_defer=0.6239, macro_f1=0.7965))
    celdas = [c.strip() for c in fila.strip("|").split("|")]

    assert celdas[2] == "0,624"
    assert celdas[3] == "0,796"


def test_los_decimales_van_con_coma():
    """El sitio está en español; una tabla con puntos decimales delata que la
    fila se pegó a mano."""
    fila = rmt._fila("Modelo X", _agregados_completos())
    assert "0.5" not in fila
