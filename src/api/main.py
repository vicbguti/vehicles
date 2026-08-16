"""src/api/main.py

Aplicación FastAPI del planificador de distribución.

Carga el servicio de modelos bajo demanda (lazy) y expone:

* ``GET  /api/health``        -- estado del servicio.
* ``POST /api/manifest``      -- valida un manifiesto (CSV o lista) y devuelve
  el estado por vehículo contra la flota dada.
* ``POST /api/distribute``    -- genera el plan de distribución con el modelo.

Ejecutar desde la raíz del repositorio::

    fleet_loading/.venv/bin/python -m uvicorn src.api.main:app --port 8000

El modelo en uso se elige al arrancar con la variable de entorno
``FLEET_LOADING_MODEL`` (``xgboost`` | ``lightgbm`` | ``attention`` | ``mlp``);
por defecto, ``xgboost``. Se confirma con ``GET /api/health``. Ver ``docs/api.md``.

El CORS se abre a cualquier origen en desarrollo (el frontend de Vite corre en
otro puerto). En producción se puede restringir vía ``ALLOWED_ORIGINS``.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
        for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
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

    validated = validate_manifest(vehicles, payload.fleet)
    return ManifestOut(vehicles=validated)


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
        raise HTTPException(
            status_code=422, detail="No hay vehículos válidos para distribuir"
        )

    vehicles = [v.model_dump() for v in accepted]
    try:
        trucks, assignment = service.distribute(vehicles, payload.fleet)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Diferidos: los vehículos válidos que el modelo no pudo colocar.
    deferred_cu = [v for v, a in zip(vehicles, assignment, strict=False) if a < 0]
    sin_camion_vehicles = [
        VehicleOut(**v, status="rejected", reason="Sin espacio disponible")
        for v in deferred_cu
    ]

    truck_outs = [
        TruckOut(
            id=t["id"],
            capacity=t["capacity"],
            vehicles=[VehicleOut(**v, status="accepted") for v in t["vehicles"]],
        )
        for t in trucks
    ]
    return DistributeOut(trucks=truck_outs, sin_camion=SinCamionOut(vehicles=sin_camion_vehicles))
