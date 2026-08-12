# Los datos

## Fuente

Matriculación de vehículos nuevos del SRI
(`data/clean/SRI_Vehiculos_Nuevos_*.csv`), 2017-2026. Una fila ≈ una
matriculación.

## El episodio de entrenamiento

Un **episodio** es el conjunto de vehículos de **un cantón en una semana ISO**,
junto con una flota de camiones. Cada vehículo aporta su CU según la clase.

La definición **quedó fijada en cantón-semana**: es la única de las tres
candidatas que produce manifiestos del tamaño que el maestro exacto puede
resolver. Las mediciones que llevaron a esa decisión están en
[viabilidad](06_feasibility.md).

| Definición | Resultado medido |
|---|---|
| Semana nacional | Siempre demasiado grande |
| **Cantón-semana** | **N ≤ 20 en la mayoría de los casos — la elegida** |
| Submuestreo | Se usa como complemento cuando N > 20 |

Total: **34 839 episodios**, 534 680 filas de vehículo.

### Columnas usadas (archivos 2018+)

| Campo | Columna del CSV | Uso |
|---|---|---|
| Cantón | `CANTÓN` | Agrupación del episodio |
| Clase | `CLASE` / `SUB CLASE` / `TIPO` | Se mapea al peso en **CU** |
| Fecha | `FECHA PROCESO (DD/MM/AA)` | Frontera de año-semana ISO |

**2017 se excluye**: su esquema es mensual y no trae fecha de proceso, así que
no se puede situar en el tiempo. 2018-2019 usan `FECHA PROCESO (MM/DD/AA)`;
2020 en adelante, `(DD/MM/AA)`.

## Del registro crudo a la feature

```csv
…;CLASE;SUB CLASE;TIPO;…;FECHA PROCESO;…;CANTON;…
…;CAMION;PLATAFORMA-C;PESADO;…;28/2/2026;…;10901;…
```

| Campo crudo | Feature |
|---|---|
| `CANTON` | Agrupación del episodio |
| `CLASE` | Valor de CU, según `config/vehicle_classes.yaml`: `AUTOMOVIL` 1,0 · `CAMIONETA` 1,4 · `JEEP` 1,1 · `MOTOCICLETA` 0,2 |
| `FECHA PROCESO` | Semana del identificador de episodio |

El ejemplo de arriba (`CLASE = CAMION`) queda **fuera de alcance**: las nodrizas
transportan automóviles, camionetas, jeeps y motocicletas, no otros camiones.

!!! warning "El cantón no es una feature del modelo"
    Aunque define el episodio, `canton` **se excluye deliberadamente** de las
    features (`src/modeling/features.py`), igual que `uid`, `truck_id` y la
    posición del vehículo dentro de su clase: solo permitirían memorizar la
    identidad del episodio. Esa decisión resultó tener consecuencias medibles,
    ver [protocolo de partición](../decisiones/04_protocolo_de_particion.md).

## Columnas descartadas

`TIPO TRANSACCIÓN`, `MARCA`, `MODELO`, `PAIS`, `AÑO MODELO`, `CILINDRAJE`,
`TIPO COMBUSTIBLE`, `COLOR 1/2`, `AVALUO`,
`PERSONA NATURAL - JURIDICA`, `TIPO SERVICIO` e identificadores de fila. Ninguna
influye en la restricción de capacidad, que es de lo único que trata el
problema de carga.

## Semanas grandes

Si una semana tiene N > 20 vehículos:

* **no** se inventa un manifiesto ficticio;
* se **submuestrea** de esa semana (estratificado por cantón y clase) para que
  el etiquetador siga siendo tratable;
* se registra el identificador de la semana padre, para trazabilidad.

Reproducible: `uv run python scripts/loading/episode_feasibility.py`.

## Partición

**Holdout temporal** por año ISO, compartido por los cuatro modelos
(`src/modeling/protocol.py`):

* entrenamiento: **2018-2024**
* validación: **2025**
* prueba: **2026**

Sin barajado aleatorio de filas entre años. La razón y su efecto medido están en
[protocolo de partición](../decisiones/04_protocolo_de_particion.md).

## Figuras exploratorias

* [Distribución de clases](solution/visuals/spatial/class_distribution.md)
* [Demandas geográficas](solution/visuals/spatial/geographic_demands.md)
* [Tendencias temporales](solution/visuals/temporal/temporal_trends.md) — estacionalidad
