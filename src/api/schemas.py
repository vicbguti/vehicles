"""src/api/schemas.py

Esquemas de petición/respuesta del API. Mantienen el contrato estable con el
frontend: los nombres de los campos siguen los del resto del repositorio
(``identificador``, ``clase``, ``cu``, ``canton``) para no inventar un vocablo.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VehicleStatus = Literal["accepted", "rejected"]


class ManifestVehicleIn(BaseModel):
    """Un vehículo tal y como llega del CSV del operador."""

    identificador: str = Field(min_length=1)
    clase: str = Field(min_length=1)
    cu: float = Field(ge=0)
    canton: str


class VehicleOut(BaseModel):
    """Vehículo devuelto al frontend, con su estado de validación."""

    identificador: str
    clase: str
    cu: float
    canton: str
    status: VehicleStatus
    reason: str | None = None


class ManifestIn(BaseModel):
    """Cuerpo de ``POST /api/manifest``.

    Se puede enviar el CSV crudo del operador en ``csv`` (se parsea y normaliza
    en el servidor) o la lista ya estructurada en ``vehicles``.
    """

    csv: str | None = None
    vehicles: list[ManifestVehicleIn] = []
    fleet: list[float] = Field(min_length=1)


class ManifestOut(BaseModel):
    vehicles: list[VehicleOut]


class DistributeIn(BaseModel):
    """Cuerpo de ``POST /api/distribute``."""

    vehicles: list[ManifestVehicleIn]
    fleet: list[float] = Field(min_length=1)


class TruckOut(BaseModel):
    """Un camión del plan de distribución."""

    id: str
    capacity: float
    vehicles: list[VehicleOut]


class SinCamionOut(BaseModel):
    vehicles: list[VehicleOut]


class DistributeOut(BaseModel):
    """Plan de distribución: camiones (canónicos) + vehículos diferidos."""

    trucks: list[TruckOut]
    sin_camion: SinCamionOut
