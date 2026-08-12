"""Pruebas del protocolo de evaluación único (`src/modeling/protocol.py`).

Lo que se protege aquí no es un detalle de implementación: es la propiedad de
que las cifras de los cuatro modelos sean comparables entre sí. El bug que este
módulo corrige —MLP con holdout temporal, GBT y transformer con partición
aleatoria, todos en la misma tabla— no lo habría detectado ninguna prueba de
las que existían, porque cada mitad era correcta por separado.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.modeling.protocol import (
    SplitConfig,
    assert_comparable,
    make_splits,
    stamp,
)


def _joined(years: dict[int, int], optimal: bool = True) -> pd.DataFrame:
    """Tabla mínima con la forma que consume make_splits: {año: n_episodios}."""
    filas = []
    for year, n_eps in years.items():
        for e in range(n_eps):
            episode_id = f"{year}-W{e:02d}"
            for v in range(2):
                filas.append(
                    {
                        "episode_id": episode_id,
                        "iso_year": year,
                        "uid": f"{episode_id}-v{v}",
                        "loaded": True,
                        "optimal": optimal,
                    }
                )
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ identidad del protocolo


def test_el_identificador_del_protocolo_es_estable_y_legible() -> None:
    cfg = SplitConfig()
    assert cfg.protocol_id == "temporal-2018_2024/2025/2026"


def test_configuraciones_distintas_dan_identificadores_distintos() -> None:
    """Si alguien cambia los años, el identificador tiene que cambiar con ellos;
    si no, dos corridas incomparables parecerían comparables."""
    a = SplitConfig()
    b = SplitConfig(train_years=(2018, 2019), val_years=(2020,), test_years=(2021,))
    assert a.protocol_id != b.protocol_id


def test_se_construye_desde_el_bloque_data_del_yaml() -> None:
    cfg = SplitConfig.from_mapping(
        {"train_years": [2018, 2019], "val_years": [2020], "test_years": [2021]}
    )
    assert cfg.train_years == (2018, 2019)
    assert cfg.val_years == (2020,)
    assert cfg.test_years == (2021,)


def test_sin_configuracion_usa_los_valores_del_proyecto() -> None:
    assert SplitConfig.from_mapping(None) == SplitConfig()


# ------------------------------------------------------------------------ construcción


def test_particiona_por_año_sin_mezclar() -> None:
    cfg = SplitConfig(train_years=(2018, 2019), val_years=(2020,), test_years=(2021,))
    bundle = make_splits(_joined({2018: 3, 2019: 2, 2020: 2, 2021: 1}), cfg)

    assert sorted(bundle["train"]["iso_year"].unique()) == [2018, 2019]
    assert sorted(bundle["val"]["iso_year"].unique()) == [2020]
    assert sorted(bundle["test"]["iso_year"].unique()) == [2021]


def test_ningun_episodio_cae_en_dos_particiones() -> None:
    """`assert_no_episode_leakage` existía en dataset.py y no la llamaba nadie.
    Ahora se ejecuta en cada partición."""
    cfg = SplitConfig(train_years=(2018,), val_years=(2019,), test_years=(2020,))
    bundle = make_splits(_joined({2018: 3, 2019: 2, 2020: 2}), cfg)

    vistos: dict[str, str] = {}
    for nombre, df in bundle.splits.items():
        for ep in df["episode_id"].unique():
            assert ep not in vistos, f"{ep} está en {vistos.get(ep)} y en {nombre}"
            vistos[ep] = nombre


def test_descarta_los_episodios_no_optimos() -> None:
    """Un episodio con optimal=False no es el óptimo, así que no sirve ni como
    objetivo ni como referencia."""
    cfg = SplitConfig(train_years=(2018,), val_years=(2019,), test_years=(2020,))
    df = pd.concat([_joined({2018: 2}), _joined({2018: 1, 2019: 1, 2020: 1}, optimal=False)])

    with pytest.raises(ValueError, match="partición"):
        # val y test quedan vacíos tras descartar los no óptimos
        make_splits(df, cfg)


def test_reporta_cuantos_episodios_descarto() -> None:
    cfg = SplitConfig(train_years=(2018,), val_years=(2019,), test_years=(2020,))
    buenos = _joined({2018: 2, 2019: 1, 2020: 1})
    malos = _joined({2018: 3}, optimal=False)
    bundle = make_splits(pd.concat([buenos, malos]), cfg)

    assert bundle.n_episodes_non_optimal_dropped == 3


def test_falla_si_una_particion_queda_vacia() -> None:
    """Pedir un año que el dataset no cubre debe fallar, no devolver métricas
    calculadas sobre cero episodios."""
    cfg = SplitConfig(train_years=(2018,), val_years=(2019,), test_years=(2099,))
    with pytest.raises(ValueError, match="test"):
        make_splits(_joined({2018: 2, 2019: 1}), cfg)


def test_falla_sin_iso_year_con_un_mensaje_accionable() -> None:
    """Es exactamente lo que pasaba en el pipeline Kedro: `encode_features`
    descartaba iso_year, así que particionar por tiempo era imposible."""
    df = _joined({2018: 2}).drop(columns=["iso_year"])
    with pytest.raises(ValueError, match="iso_year"):
        make_splits(df)


def test_rechaza_años_solapados() -> None:
    cfg = SplitConfig(train_years=(2018, 2019), val_years=(2019,), test_years=(2020,))
    with pytest.raises(ValueError, match="solapan"):
        make_splits(_joined({2018: 2, 2019: 2, 2020: 1}), cfg)


# --------------------------------------------------------------------- comparabilidad


def test_stamp_marca_protocolo_y_particion() -> None:
    payload = stamp({"model": "mlp"}, SplitConfig(), "test")
    assert payload["protocol"] == "temporal-2018_2024/2025/2026"
    assert payload["split"] == "test"


def test_resultados_del_mismo_protocolo_son_comparables() -> None:
    cfg = SplitConfig()
    filas = [stamp({"model": m}, cfg, "test") for m in ("mlp", "xgboost", "lightgbm", "attention")]
    assert_comparable(filas)  # no debe levantar


def test_mezclar_protocolos_falla() -> None:
    """El bug original, ahora imposible de cometer en silencio."""
    filas = [
        {"model": "mlp", "protocol": "temporal-2018_2024/2025/2026", "split": "test"},
        {"model": "xgboost", "protocol": "group-shuffle-0.2", "split": "val"},
    ]
    with pytest.raises(ValueError, match="protocolos distintos"):
        assert_comparable(filas)


def test_mezclar_particiones_del_mismo_protocolo_tambien_falla() -> None:
    """Comparar el val de un modelo contra el test de otro tampoco vale."""
    cfg = SplitConfig()
    filas = [stamp({"model": "mlp"}, cfg, "test"), stamp({"model": "xgboost"}, cfg, "val")]
    with pytest.raises(ValueError, match="protocolos distintos"):
        assert_comparable(filas)


def test_resultados_sin_marcar_se_rechazan_con_su_nombre() -> None:
    """Los artefactos anteriores a este cambio no declaran protocolo: hay que
    regenerarlos, no asumir que son comparables."""
    filas = [
        {"model": "mlp", "protocol": "temporal-2018_2024/2025/2026", "split": "test"},
        {"model": "attention"},
    ]
    with pytest.raises(ValueError, match="attention"):
        assert_comparable(filas)


def test_comparar_una_lista_vacia_no_falla() -> None:
    assert_comparable([])
