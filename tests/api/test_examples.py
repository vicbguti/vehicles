"""Pruebas de los manifiestos de ejemplo que sirve el API.

Los manifiestos son CSV --el input del app-- construidos con vehículos reales
del SRI. pytest los crea como fixture (y en ``tmp_path``) y verifica el round
trip completo: el CSV generado se lee con ``parse_csv`` y el API lo sirve y lo
acepta en ``POST /api/distribute``.
"""

from __future__ import annotations

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from src.api.examples import (
    DEFAULT_REAL_EPISODE,
    EXAMPLES,
    build_example_csv,
    build_real_episode_csv,
    real_episode_count,
    real_episode_fleet,
)
from src.api.main import app
from src.api.validation import parse_csv


@pytest.fixture(scope="session")
def profesor_csv() -> str:
    """CSV del ejemplo del profesor, creado por la fixture (pytest)."""
    return build_example_csv("profesor")


@pytest.fixture(scope="session")
def real_episode_csv() -> str:
    """Caso-scenario real por defecto, creado por la fixture (pytest)."""
    return build_real_episode_csv(*DEFAULT_REAL_EPISODE)


@pytest.fixture(scope="session")
def profesor_file(tmp_path_factory: pytest.TempPathFactory):
    """El mismo CSV escrito a disco por ``tmp_path_factory`` de pytest."""
    out = tmp_path_factory.mktemp("manifiestos") / "profesor.csv"
    out.write_text(build_example_csv("profesor"), encoding="utf-8")
    return out


def test_profesor_csv_es_un_manifiesto_valido(profesor_csv: str) -> None:
    vehicles = parse_csv(profesor_csv)
    assert len(vehicles) == 18
    assert Counter(v.clase for v in vehicles) == {"AUTOMOVIL": 12, "JEEP": 6}
    # CU reales del SRI
    assert {v.cu for v in vehicles} == {1.0, 1.1}


def test_profesor_csv_escrito_a_disco_se_vuelve_a_leer(profesor_file) -> None:
    vehicles = parse_csv(profesor_file.read_text(encoding="utf-8"))
    assert len(vehicles) == 18


def test_api_sirve_los_manifiestos_de_ejemplo() -> None:
    client = TestClient(app)
    for name in EXAMPLES:
        r = client.get(f"/api/manifests/{name}.csv")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert parse_csv(r.text)  # el API sirve un CSV que vuelve a entrar


def test_api_404_para_manifiesto_desconocido() -> None:
    client = TestClient(app)
    assert client.get("/api/manifests/inexistente.csv").status_code == 404


def test_profesor_se_puede_distribuir_desde_el_api(profesor_csv: str) -> None:
    pytest.importorskip("xgboost")  # extra `gbt`; el modelo por defecto es xgboost
    client = TestClient(app)
    vehicles = [v.model_dump() for v in parse_csv(profesor_csv)]
    r = client.post(
        "/api/distribute",
        json={"vehicles": vehicles, "fleet": [6.0, 6.0]},
    )
    assert r.status_code == 200
    plan = r.json()
    n_loaded = sum(len(t["vehicles"]) for t in plan["trucks"])
    assert n_loaded == 12  # los 12 AUTOMOVIL (CU 1.0) llenan la flota; los JEEP difieren
    assert len(plan["sin_camion"]["vehicles"]) == 6


def test_episodio_real_no_tiene_cap_de_submuestreo(real_episode_csv: str) -> None:
    """Un caso-scenario real es el episodio completo del registro, sin el cap
    de <= 20 vehículos que aplica la generación de episodios de entrenamiento."""
    vehicles = parse_csv(real_episode_csv)
    assert len(vehicles) > 20
    # todos del mismo (año, semana, cantón) del episodio por defecto
    assert {v.canton for v in vehicles} == {DEFAULT_REAL_EPISODE[2]}


def test_api_sirve_el_episodio_real() -> None:
    client = TestClient(app)
    r = client.get("/api/manifests/real-episode.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert len(parse_csv(r.text)) > 20


def test_api_404_para_episodio_real_inexistente() -> None:
    client = TestClient(app)
    r = client.get("/api/manifests/real-episode.csv?iso_year=1990&iso_week=1&canton=99999")
    assert r.status_code == 404


def test_flota_del_episodio_real_es_determinista_y_dimensionada() -> None:
    """La flota del caso real se dimensiona al CU del episodio (no es la banda
    de 1-4 camiones del entrenamiento, que es para episodios <= 20)."""
    y, w, c = DEFAULT_REAL_EPISODE
    fleet = real_episode_fleet(y, w, c)
    assert fleet == real_episode_fleet(y, w, c)  # determinista por episodio
    assert len(fleet) > 4  # un cantón completo necesita una flota proporcional
    assert all(cap > 0 for cap in fleet)
    total_cu = sum(v.cu for v in parse_csv(build_real_episode_csv(y, w, c)))
    assert round(sum(fleet), 1) == round(total_cu * 0.95, 1)
    assert real_episode_count(y, w, c) > 20


def test_api_sirve_el_caso_completo() -> None:
    client = TestClient(app)
    profesor = client.get("/api/scenarios/profesor").json()
    assert profesor["fleet"] == [6.0, 6.0]
    assert profesor["vehicles_count"] == 18
    assert client.get(profesor["csv_url"]).status_code == 200

    real = client.get("/api/scenarios/real-episode").json()
    assert real["fleet"]
    assert real["vehicles_count"] > 20
    assert client.get(real["csv_url"]).status_code == 200


def test_api_404_para_escenario_desconocido() -> None:
    client = TestClient(app)
    assert client.get("/api/scenarios/inexistente").status_code == 404


def test_parse_csv_con_formato_inconsistente_da_mensaje_claro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un CSV que pandas no puede tokenizar debe fallar con un mensaje accionable,
    no con el error crudo ('Error tokenizing data...')."""
    from pandas.errors import ParserError

    def _raisy(*_args, **_kwargs):
        raise ParserError("C error: Expected 1 fields in line 4, saw 2")

    monkeypatch.setattr("src.api.validation.pd.read_csv", _raisy)
    with pytest.raises(ValueError, match="formato de columnas es inconsistente"):
        parse_csv("identificador;clase;cu;canton\nA;AUTOMOVIL;1.0;21701\n")
