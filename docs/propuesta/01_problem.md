# El problema

## Contexto real

Las distribuidoras de vehículos en Ecuador entregan unidades nuevas —importadas
o ensambladas— a concesionarios repartidos por **221 cantones**. El despacho
tiene que respetar:

* **Límites de capacidad** — carga útil y espacio de plataforma de cada nodriza.
* **Vehículos heterogéneos** — una camioneta no ocupa lo mismo que una moto.
* **Costo operativo** — una mala carga deja vehículos en tierra, obliga a
  alquilar camiones extra y desperdicia capacidad de flota.

## Alcance: carga de flota con capacidad

El proyecto se limita a la **carga de flota con restricción de capacidad**: dado
el manifiesto de vehículos de una semana en un cantón, decidir **qué camión
lleva cada vehículo** o diferirlo a un turno posterior. La **secuenciación de
rutas** (orden de visita, distancia) queda fuera — ver
[diferido](deferred/README.md).

## Unidades de capacidad (CU)

La capacidad de los camiones y el tamaño de los vehículos se normalizan en
**unidades de capacidad**. Los valores vigentes están en
`config/vehicle_classes.yaml`:

| Clase en alcance | CU |
|---|---|
| `AUTOMOVIL` | 1,0 |
| `CAMIONETA` | 1,4 |
| `JEEP` | 1,1 |
| `MOTOCICLETA` | 0,2 |

Fuera de alcance: `CAMION`, `ESPECIAL`, `OMNIBUS`, `TANQUERO`, `TRAILER`,
`VOLQUETA`.

La flota **no es fija**. Cada episodio recibe entre **1 y 4 camiones** con
capacidades muestreadas en el rango **3,0-9,0 CU**
(`N_TRUCKS_RANGE` y `CAP_RANGE` en `src/loading/scenarios.py`). Exceder la
capacidad de un camión es inviable, y ningún plan que produce el sistema lo hace:
el decodificador solo coloca un vehículo si cabe en la capacidad restante.

!!! note "La propuesta original decía otra cosa"
    La versión inicial fijaba **6,0 CU por camión**, dos camiones y dos clases
    (SUV 1,0 / sedán 0,67). Esa formulación quedó superada: ver
    [alcance original](../historico/02_alcance_original.md). Los modelos
    actuales no tienen ningún número de camiones codificado.

Restricciones formales de *bin packing*:
[bin_packing.md](deferred/theory/2_generalization/3_partitioning/bin_packing.md).

## Por qué importa

El despacho manual agrupa por región aproximada sin optimizar **cómo encajan los
vehículos en los camiones**. Eso deja camiones a medio llenar y empuja unidades
a transportistas terceros. El caso de estudio de
[evaluación](05_evaluation.md) muestra 6 vehículos en tierra con el
procedimiento actual frente a 2 con la carga óptima.
