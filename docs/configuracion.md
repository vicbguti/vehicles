# Configuración

Tres archivos YAML en `config/`. `schemas.yaml` **ya no existe**: su
`raw_schema.columns` nunca se llenó y ningún módulo lo leía.

## `config/vehicle_classes.yaml` — qué se transporta y cuánto ocupa

Define las cuatro clases en alcance y su **unidad de capacidad** (CU), más las
clases explícitamente fuera de alcance.

| Clase | CU |
|---|---|
| `AUTOMOVIL` | 1,0 |
| `CAMIONETA` | 1,4 |
| `JEEP` | 1,1 |
| `MOTOCICLETA` | 0,2 |

Fuera de alcance: `CAMION`, `ESPECIAL`, `OMNIBUS`, `TANQUERO`, `TRAILER`,
`VOLQUETA` — vehículos que no viajan en un camión nodriza.

Estos valores llegan al maestro exacto como **flotantes**, y ahí importa: el
etiquetador los convierte a fracciones exactas con `limit_denominator` para que
la aritmética de capacidad no acumule error de coma flotante. Hay una prueba
dedicada a esa ruta (`tests/loading/test_labeler.py`), añadida porque las
pruebas que usaban `Fraction` directamente no la ejercitaban.

## `config/mlp.yaml` — hiper-parámetros del MLP

Arquitectura, optimización, partición y política del decodificador. Cada valor
lleva escrita su justificación; el detalle está en
[arquitectura del MLP](modelo/arquitectura_mlp.md).

La sección `data` fija la **partición temporal** (entrenamiento 2018-2024,
validación 2025, prueba 2026), que hoy comparten los seis modelos a través de
`src/modeling/protocol.py`. Ver
[protocolo de partición](decisiones/04_protocolo_de_particion.md).

`decoder.policy: count` ordena por CU ascendente, alineado con el objetivo
lexicográfico del maestro (primero cuántos vehículos, después cuánta capacidad).
Se elige por validación entre `model`, `count` y `respect_defer`.

## `config/config.yaml` — perfilado y reportes

Solo lo que algún módulo lee de verdad. Se eliminaron `raw_dir` y
`processed_dir` (apuntaban a directorios inexistentes) y `features_dir` (sin
lectores).

!!! warning "El diccionario Excel no viene en el clon"
    `data.dictionary` apunta a `data/raw/SRI_Vehiculos_DD.xlsx`, que está en
    `.gitignore`. La etapa de demandas geográficas
    (`scripts/reporting/proposals/solution_visuals/spatial/geographic_demands.py`)
    es la única que lo usa y falla sin él. Ver [reportes](reportes.md).

## `conf/base/parameters.yml` — el pipeline Kedro

Hiper-parámetros de XGBoost, LightGBM y el transformer, más la partición
compartida. Ver [pipeline Kedro](pipeline_kedro.md).
