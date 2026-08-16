"""src/api/__init__.py

API web para el planificador de distribución de vehículos en camiones.

Expone dos flujos que corresponden a los casos de uso de entrada y de salida:

* ``POST /api/manifest`` -- valida un manifiesto (CSV) contra la flota indicada
  y devuelve el estado por vehículo (Aceptado / Rechazado + motivo).
* ``POST /api/distribute`` -- dado un conjunto de vehículos aceptados y una
  flota, produce el plan de distribución con el modelo entrenado.

La inferencia reutiliza la maquinaria probada de ``src.modeling`` y
``fleet_loading`` (canonicalización, tensores por par, decoder con capacidad y
las GBTs/attention), sin reimplementar nada.
"""
