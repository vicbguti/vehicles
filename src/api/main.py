"""src/api/main.py

Aplicación FastAPI del planificador de distribución.

Carga el servicio de modelos bajo demanda (lazy) y expone:

* ``GET  /api/health``        -- estado del servicio.
* ``GET  /api/manifests/{nombre}.csv`` -- manifiesto de ejemplo (CSV) con
  vehículos reales del SRI, listo para ``POST /api/distribute``.
* ``GET  /api/manifests/real-episode.csv`` -- caso-scenario real: todos los
  vehículos registrados en un (año, semana, cantón), sin cap de submuestreo.
* ``POST /api/manifest``      -- valida un manifiesto (CSV o lista) y devuelve
  el estado por vehículo contra la flota dada.
* ``POST /api/distribute``    -- genera el plan de distribución con el modelo.

Ejecutar desde la raíz del repositorio::

    fleet_loading/.venv/bin/python -m uvicorn src.api.main:app --port 8000

El modelo en uso se elige al arrancar con la variable de entorno
``FLEET_LOADING_MODEL`` (``xgboost`` | ``lightgbm`` | ``attention`` | ``mlp`` |
``rf`` | ``logreg``); por defecto, ``xgboost``. Se confirma con
``GET /api/health``. Ver ``docs/api.md``.

El CORS se abre a cualquier origen en desarrollo (el frontend de Vite corre en
otro puerto). En producción se puede restringir vía ``ALLOWED_ORIGINS``.
"""

from __future__ import annotations

import os
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from src.api.examples import (
    DEFAULT_REAL_EPISODE,
    EXAMPLES,
    build_example_csv,
    build_real_episode_csv,
)
from src.api.models import ModelService, ModelUnavailableError
from src.api.schemas import (
    DistributeIn,
    DistributeOut,
    ManifestIn,
    ManifestOut,
    SinCamionOut,
    TruckOut,
    VehicleOut,
)
from src.api.validation import parse_csv, validate_manifest

DEFAULT_MODEL = os.environ.get("FLEET_LOADING_MODEL", "xgboost")

app = FastAPI(
    title="Planificador de Distribución de Transporte",
    description="Asigna vehículos de un manifiesto a camiones de carga sin exceder "
    "capacidades, usando los modelos entrenados del repositorio.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.environ.get(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_service: ModelService | None = None


def get_service() -> ModelService:
    """Carga el servicio de modelos la primera vez que se pide."""
    global _service
    if _service is None:
        try:
            _service = ModelService(DEFAULT_MODEL)
        except ModelUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _service


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "model": DEFAULT_MODEL}


@app.get("/api/manifests/real-episode.csv")
def real_episode(
    iso_year: int | None = None,
    iso_week: int | None = None,
    canton: str | None = None,
) -> Response:
    """Descarga un caso-scenario real: todos los vehículos registrados en el SRI
    para un (año, semana, cantón), SIN cap de submuestreo. Sin parámetros usa
    ``DEFAULT_REAL_EPISODE`` (cantón 21701, semana 9 de 2026, 2,734 vehículos);
    con parámetros, cualquier episodio del registro.
    """
    iso_year, iso_week, canton = (
        iso_year if iso_year is not None else DEFAULT_REAL_EPISODE[0],
        iso_week if iso_week is not None else DEFAULT_REAL_EPISODE[1],
        canton if canton is not None else DEFAULT_REAL_EPISODE[2],
    )
    csv = build_real_episode_csv(iso_year, iso_week, canton)
    if not csv:
        raise HTTPException(status_code=404, detail="El episodio no existe en el registro")
    return Response(content=csv, media_type="text/csv")


@app.get("/api/manifests/{name}.csv")
def example_manifest(name: str) -> Response:
    """Descarga un manifiesto de ejemplo (CSV) construido con vehículos reales del SRI.

    El resultado se puede enviar tal cual a ``POST /api/distribute`` con la
    flota indicada en ``docs/api.md`` (profesor: ``[6, 6]``; profesor-escalado:
    ``[6, 7, 7]``).
    """
    if name not in EXAMPLES:
        raise HTTPException(status_code=404, detail="Manifiesto de ejemplo desconocido")
    return Response(content=build_example_csv(name), media_type="text/csv")


@app.post("/api/manifest", response_model=ManifestOut)
def validate_manifest_endpoint(
    payload: ManifestIn,
    service: ModelService = Depends(get_service),
) -> ManifestOut:
    """Valida el manifiesto contra la flota. Acepta CSV crudo o lista de
    vehículos ya estructurados en ``vehicles``."""
    try:
        vehicles = parse_csv(payload.csv) if payload.csv else payload.vehicles
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not vehicles:
        raise HTTPException(status_code=422, detail="El manifiesto está vacío")

    started = time.perf_counter()
    validated = validate_manifest(vehicles, payload.fleet)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return ManifestOut(vehicles=validated, elapsed_ms=elapsed_ms)


@app.post("/api/distribute", response_model=DistributeOut)
def distribute_endpoint(
    payload: DistributeIn,
    service: ModelService = Depends(get_service),
) -> DistributeOut:
    """Genera el plan de distribución para los vehículos aceptados."""
    if not payload.vehicles:
        raise HTTPException(status_code=422, detail="No hay vehículos para distribuir")

    accepted = [v for v in payload.vehicles if v.cu > 0]
    if not accepted:
        raise HTTPException(status_code=422, detail="No hay vehículos válidos para distribuir")

    vehicles = [v.model_dump() for v in accepted]
    # Se cronometra sólo la resolución del plan: `get_service` ya resolvió la
    # dependencia (y, en el primer uso, la carga del artefacto) antes de entrar
    # aquí, así que el tiempo medido es comparable entre peticiones.
    started = time.perf_counter()
    try:
        trucks, assignment = service.distribute(vehicles, payload.fleet)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    elapsed_ms = (time.perf_counter() - started) * 1000

    # Diferidos: los vehículos válidos que el modelo no pudo colocar.
    deferred_cu = [v for v, a in zip(vehicles, assignment, strict=False) if a < 0]
    sin_camion_vehicles = [
        VehicleOut(**v, status="rejected", reason="Sin espacio disponible") for v in deferred_cu
    ]

    truck_outs = [
        TruckOut(
            id=t["id"],
            capacity=t["capacity"],
            vehicles=[VehicleOut(**v, status="accepted") for v in t["vehicles"]],
        )
        for t in trucks
    ]
    return DistributeOut(
        trucks=truck_outs,
        sin_camion=SinCamionOut(vehicles=sin_camion_vehicles),
        model=service.model_name,
        elapsed_ms=elapsed_ms,
    )
