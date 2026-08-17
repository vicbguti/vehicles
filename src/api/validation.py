"""src/api/validation.py

Normalización y validación del manifiesto, siguiendo las alternativas del caso
de uso de entrada:

* 2a. vehículo incompleto (falta identificador, clase, cantón o espacio).
* 2b. vehículo cuyo espacio supera la capacidad de todos los camiones.
* 2c. identificador único duplicado.
* 2d. manifiesto vacío.

Los motivos devueltos coinciden con los del frontend: ``Sin Datos``,
``Sin Almacenamiento``, ``Sin Cantón`` y ``Supera la capacidad máxima``.
"""

from __future__ import annotations

import io

import pandas as pd
from pandas.errors import ParserError

from src.api.schemas import ManifestVehicleIn, VehicleOut

# Alias de encabezado aceptados para cada campo, normalizados (minúsculas).
_IDENTIFICADOR_ALIASES = {"identificador", "id", "codigo", "codigo_vehiculo", "uid"}
_CLASE_ALIASES = {"clase", "tipo"}
_CU_ALIASES = {"cu", "unidades", "espacio", "unidades_de_almacenamiento", "storage"}
_CANTON_ALIASES = {"canton", "canton_destino", "canton_de_destino", "destino"}

REASON_SIN_DATOS = "Sin Datos"
REASON_SIN_ALMACENAMIENTO = "Sin Almacenamiento"
REASON_SIN_CANTON = "Sin Cantón"
REASON_SUPERA_CAPACIDAD = "Supera la capacidad máxima"
REASON_DUPLICADO = "Identificador duplicado"


def _column_map(headers: list[str]) -> dict[str, str]:
    """Mapea encabezados del CSV a los campos canónicos del manifiesto."""
    normalized = {h.strip().lower().replace(" ", "_"): h for h in headers if h}
    mapping: dict[str, str] = {}
    for field, aliases in (
        ("identificador", _IDENTIFICADOR_ALIASES),
        ("clase", _CLASE_ALIASES),
        ("cu", _CU_ALIASES),
        ("canton", _CANTON_ALIASES),
    ):
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def parse_csv(csv_text: str) -> list[ManifestVehicleIn]:
    """Parsea el texto CSV del operador a vehículos estructurados.

    Acepta encabezados en español (y variantes). Levanta ``ValueError`` si el
    archivo está vacío o si falta alguna columna esencial.
    """
    if not csv_text.strip():
        raise ValueError("El manifiesto está vacío")

    # Los CSV del operador son punto y coma; también aceptamos coma.
    delim = ";"
    if "," in csv_text.splitlines()[0] and ";" not in csv_text.splitlines()[0]:
        delim = ","
    try:
        df = pd.read_csv(io.StringIO(csv_text), sep=delim, dtype=str)
    except ParserError as exc:
        raise ValueError(
            "El CSV no se pudo leer: el formato de columnas es inconsistente "
            "(se espera una fila de cabecera y una columna por vehículo, "
            "separadas por punto y coma)."
        ) from exc
    mapping = _column_map(df.columns.tolist())
    missing = [f for f in ("identificador", "clase", "cu", "canton") if f not in mapping]
    if missing:
        raise ValueError(
            "El CSV no tiene las columnas requeridas: "
            + ", ".join(missing)
            + " (esperadas: identificador, clase, cantón, espacio)"
        )

    vehicles: list[ManifestVehicleIn] = []
    for _, row in df.iterrows():
        cu_raw = str(row[mapping["cu"]]).strip().replace(",", ".")
        try:
            cu = float(cu_raw) if cu_raw not in ("", "-") else 0.0
        except ValueError:
            cu = 0.0
        vehicles.append(
            ManifestVehicleIn(
                identificador=str(row[mapping["identificador"]]).strip(),
                clase=str(row[mapping["clase"]]).strip(),
                cu=cu,
                canton=str(row[mapping["canton"]]).strip(),
            )
        )
    return vehicles


def validate_manifest(
    vehicles: list[ManifestVehicleIn],
    fleet: list[float],
) -> list[VehicleOut]:
    """Asigna el estado de validación a cada vehículo contra la flota."""
    max_capacity = max(fleet)
    seen: dict[str, int] = {}
    results: list[VehicleOut] = []

    for vehicle in vehicles:
        status = "accepted"
        reason: str | None = None

        identificador = vehicle.identificador
        if not identificador or identificador == "-":
            status, reason = "rejected", REASON_SIN_DATOS
        elif identificador in seen:
            status, reason = "rejected", REASON_DUPLICADO
        else:
            seen[identificador] = 1

        if status == "accepted" and (not vehicle.clase or vehicle.clase == "-"):
            status, reason = "rejected", REASON_SIN_DATOS
        if status == "accepted" and vehicle.cu <= 0:
            status, reason = "rejected", REASON_SIN_ALMACENAMIENTO
        if status == "accepted" and (not vehicle.canton or vehicle.canton == "-"):
            status, reason = "rejected", REASON_SIN_CANTON
        if status == "accepted" and vehicle.cu > max_capacity:
            status, reason = "rejected", REASON_SUPERA_CAPACIDAD

        results.append(
            VehicleOut(
                identificador=vehicle.identificador,
                clase=vehicle.clase,
                cu=vehicle.cu,
                canton=vehicle.canton,
                status=status,
                reason=reason,
            )
        )
    return results
