# Matriculaciones totales (todas las provincias)

- **Total de matriculaciones (todas las provincias):** 4 306 526

> Agrega las matriculaciones del dataset del SRI **2017-2026** en todas las
> provincias.

!!! note "Por qué aquí sí entra 2017"
    El perfilado y los reportes leen los diez CSV de `data/clean/`, 2017
    incluido. El **modelado** sí descarta 2017, porque su CSV no trae la columna
    `FECHA PROCESO` y no se puede situar en el tiempo (`src/modeling/dataset.py`).
    Por eso la cobertura del modelado es 2018-2026 y la de esta cifra es
    2017-2026: no es una contradicción, son dos alcances distintos.
