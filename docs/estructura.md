# Estructura del código

El repositorio mezcla tres generaciones de código que se están reconciliando:
el andamiaje inicial de ingesta y perfilado, el núcleo de modelado, y el
pipeline Kedro que consume ese núcleo.

## `src/loading/` — el maestro exacto

La verdad de referencia de todo el proyecto. No es un modelo: es una búsqueda
exacta que calcula el óptimo con el que se entrenan los seis modelos.

| Módulo | Qué hace |
|---|---|
| `labeler.py` | Programación dinámica sobre enteros escalados con `fractions.Fraction`, sin solvers externos. Maximiza en orden lexicográfico: primero cuántos vehículos se cargan, después cuánta capacidad se aprovecha |
| `scenarios.py` | Construye los episodios (cantón, semana ISO) y genera la flota. Ordena las capacidades antes de etiquetar — ver [canonicalización](modelo/canonicalizacion.md) |

Cubierto por 325 pruebas validadas por mutación: se comprobó que fallan ante
regresiones deliberadas, no solo que pasan en verde.

## `src/modeling/` — el núcleo compartido

Todo lo que los seis modelos tienen en común. Ningún modelo reimplementa nada
de esto.

| Módulo | Qué hace |
|---|---|
| `canonicalization.py` | Reindexa la flota por capacidad descendente. `CAMION_1` significa «el camión más grande», no «el que salió primero del generador» |
| `features.py` | Tensores por par `(vehículo, camión)`. Excluye deliberadamente `canton`, `uid`, `truck_id` y la posición dentro de la clase: solo permitirían memorizar |
| `capacity_decoder.py` | `decode_episode` — decodificador voraz que respeta la capacidad. El plan es factible por construcción: un vehículo solo se coloca si cabe |
| `metrics.py` | **El único sitio donde se calcula una cifra publicable.** Métricas por episodio contra el maestro exacto, más la línea base greedy. Los seis modelos pasan por `aggregate()` |
| `figures.py` | Formato común del historial de entrenamiento y de las figuras. La unidad del eje viaja dentro del CSV, así que ninguna gráfica se puede rotular mal |
| `dataset.py` | Carga de episodios y `assert_no_episode_leakage` |
| `protocol.py` | **El único sitio donde se construye una partición.** Holdout temporal compartido por los seis modelos |
| `flat_features.py` | Aplana los tensores por par a una fila de ancho fijo, para los clasificadores multiclase de scikit-learn. Ver [modelos clásicos](modelo/modelos_clasicos.md) |
| `mlp_classifier.py` | El MLP en Keras |

## `src/pipeline/` y `src/profiler/` — ingesta y perfilado

Heredados del análisis inicial del dataset del SRI. `pipeline/` limpia y
deduplica los CSV; `profiler/` calcula completitud, unicidad, deriva de esquema
y métricas físicas de almacenamiento.

## `fleet_loading/` — el pipeline Kedro

XGBoost, LightGBM y el transformer. Consume los tensores canónicos de
`src/modeling` mediante un parche de `sys.path`, que desaparecerá al empaquetar
el proyecto. Detalle en [pipeline Kedro](pipeline_kedro.md).

## `src/api/` — el servicio de distribución

FastAPI que sirve los seis modelos: los cuatro *pairwise* (XGBoost, LightGBM,
attention y el MLP) sin límite de camiones ni de capacidad, y los de ancho fijo
(Random Forest y regresión logística) con el tope `max_trucks` de su artefacto
aplicado explícitamente. Valida el manifiesto con los motivos del caso de uso y
genera el plan con `decode_episode`, reutilizando `src.modeling`. El modelo en
uso se elige al arrancar con `FLEET_LOADING_MODEL`. Detalle en
[servicio de distribución (API)](api.md).

## `scripts/` — entradas de línea de comandos

`build_vehicle_features.py`, `build_scenarios.py`, `train_mlp.py`,
`evaluate_mlp.py`, `sweep_mlp.py`, `train_classical.py`, `label_ceiling.py`,
`teacher_self_agreement.py`, `build_extrapolation_set.py`,
`evaluate_fleet_loading.py`, `compare_split_protocols.py`,
`report_model_table.py`, y los tres orquestadores del perfilado y los reportes
(`run_pipeline.py`, `run_profiling.py`, `run_reporting.py`).

Dos que conviene conocer: `train_classical.py` entrena el Random Forest y la
regresión logística ([modelos clásicos](modelo/modelos_clasicos.md)), y
`report_model_table.py` **genera** la tabla comparativa desde los JSON medidos
— con `--check` en CI, para que lo publicado no vuelva a divergir de lo medido.

Cada uno añade la raíz del repositorio a `sys.path`, porque hoy no hay nada
instalable. Es deuda conocida.
