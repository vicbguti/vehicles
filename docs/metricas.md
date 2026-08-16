# Métricas operativas

Los modelos se juzgan con las tres métricas formales de la entrega, calculadas
contra el **maestro exacto** de `data/episodes/episodes.parquet`, que lleva
`n_loaded` y `cu_utilized` por episodio (es decir, `V_exact` para cada
manifiesto).

Los seis modelos se evalúan sobre **la misma partición**: el holdout temporal
de `src/modeling/protocol.py` (entrenamiento 2018-2024, validación 2025, prueba
2026). La maquinaria es `src/modeling/metrics.py`, la misma que evalúa el MLP,
a través de `fleet_loading/src/fleet_loading/pipelines/training/pairwise.py` y
de `scripts/train_classical.py`.

!!! warning "Esta página decía otra cosa hasta agosto de 2026"
    Publicaba «6.968 episodios, GroupShuffleSplit por episode_id». Ese era el
    protocolo aleatorio del pipeline Kedro, mientras el MLP usaba holdout
    temporal, y **ambas cifras se publicaban en la misma tabla**. Hoy la
    validación son 4.030 episodios del año 2025 y `assert_comparable`
    (`src/modeling/protocol.py`) falla si alguien intenta mezclar protocolos.
    El efecto medido del cambio está en
    [protocolo de partición](decisiones/04_protocolo_de_particion.md).

## Las tres métricas de la entrega

1. **Eficiencia de llenado volumétrico** — CU usada / capacidad total de la
   flota (`cu_utilization_model_pct`). Los episodios son ricos en capacidad por
   construcción, así que maestro y modelos convergen cerca del ~36 %; la señal
   que discrimina es la brecha de conteo.
2. **Tiempo de cómputo** — milisegundos del manifiesto al plan completo
   (`latency.mean_ms`, `p99_ms`), medido con `time.perf_counter`.
3. **Brecha óptima** — `(V_maestro − V_modelo) / V_maestro` sobre el objetivo
   primario (vehículos cargados). El maestro es la programación dinámica exacta,
   demostrada igual a la enumeración por fuerza bruta, así que esto es la
   «brecha óptima en instancias acotadas» que pide la entrega.

## El invariante de factibilidad

Todo plan que producen los decodificadores es **factible por construcción**: un
vehículo solo se coloca si cabe en la capacidad restante. La puerta dura es
`capacity_violation_rate = 0.0`; si alguna vez es distinta de cero, el resto de
las métricas no significa nada.

`max_overflow_cu` puede ser un flotante minúsculo (~1e-7) en el transformer,
porque su decodificador empaqueta en float32 y el reporte vuelve a comprobar en
float64. Cualquier desbordamiento por debajo de `_TOL = 1e-9` se trata como
ruido de medición, no como violación.

## La tabla comparativa

<!-- INICIO tabla generada -->
| Modelo | Exactitud | F1 diferir | F1 macro | Brecha de conteo | Iguala al maestro | Llenado (CU) | Violación cap. | Latencia media / p99 (ms) |
|---|---|---|---|---|---|---|---|---|
| **XGBoost** | 0,827 | 0,618 | 0,794 | 0,0261 | 97,5 % | 35,6 % | 0,0 | 0,04 / 0,06 |
| **LightGBM** | 0,823 | 0,616 | 0,790 | 0,0263 | 97,5 % | 35,6 % | 0,0 | 0,04 / 0,08 |
| **Transformer** | 0,830 | 0,601 | 0,793 | 0,0313 | 97,0 % | 35,5 % | 0,0 | 0,04 / 0,06 |
| **MLP (Keras)** | 0,829 | 0,624 | 0,796 | 0,0266 | 97,4 % | 35,6 % | 0,0 | — / — |
| **Random Forest** | 0,831 | 0,602 | 0,795 | 0,0320 | 96,9 % | 35,5 % | 0,0 | — / — |
| **Regresión logística** | 0,811 | 0,601 | 0,778 | 0,0333 | 96,9 % | 35,5 % | 0,0 | — / — |
| **Greedy (línea base)** | 0,272 | 0,325 | 0,185 | 0,6310 | 87,4 % | 36,2 % | 0,0 | 0,04 / 0,06 |

Medido sobre la validación del protocolo temporal (**4030 episodios**, año 2025) contra el maestro exacto. Las nueve columnas salen del mismo bloque de agregados de `src/modeling/metrics.py`, **después del decodificador**, para los seis modelos y para el greedy.

**F1 diferir** y **F1 macro** van en columnas separadas porque son métricas distintas y no intercambiables: la primera mide la clase minoritaria —dejar un vehículo en el andén—, la segunda promedia las cinco clases y por eso sale ~0,17 más alta. Cualquiera de las dos se puede reconstruir desde la matriz de confusión que publica cada modelo en su JSON.

La **latencia se omite a propósito** en el MLP, Random Forest y la regresión logística. `scripts/evaluate_mlp.py` cronometra la inferencia completa (`model.predict` + decodificación, ~40 ms, dominada por la sobrecarga de Keras), el pipeline Kedro cronometra solo `decode_episode` (~0,04 ms) y `scripts/train_classical.py` no la cronometra. Son mediciones distintas y ponerlas en la misma columna las haría parecer comparables.

Tabla generada por `scripts/report_model_table.py` a partir de los JSON medidos. **No editar a mano**: se regenera con `--write`, y `--check` lo verifica en CI.
<!-- FIN tabla generada -->

## Reporte por episodio (`EpisodeResult`)

Lo construye `src.modeling.metrics.build_result` a partir de `capacity_decoder.DecodedEpisode`:

| Campo | Qué es |
|---|---|
| `episode_id` | identificador del manifiesto |
| `n_vehicles`, `n_trucks` | tamaño del manifiesto |
| `total_capacity` | Σ capacidades de los camiones (CU) |
| `model_n_loaded` | vehículos que carga el modelo |
| `teacher_n_loaded` | vehículos que carga el maestro exacto (`V_exact`) |
| `model_cu`, `teacher_cu` | CU aprovechada por modelo / maestro |
| `max_overflow` | mayor exceso sobre la capacidad (CU) |

## Agregados (`aggregate`)

| Métrica | Fórmula |
|---|---|
| `capacity_violation_rate` | media(max_overflow > 1e-9) — debe ser 0 |
| `loaded_gap_mean` | media(teacher_n_loaded − model_n_loaded) |
| `episodes_matching_teacher_count_pct` | % de episodios donde model_n_loaded = teacher_n_loaded |
| `optimality_gap_loaded_pct` | 100 · media((maestro − modelo)/maestro) |
| `cu_gap_mean` | media(teacher_cu − model_cu) |
| `cu_utilization_model_pct` | 100 · Σ model_cu / Σ total_capacity |
| `cu_utilization_teacher_pct` | 100 · Σ teacher_cu / Σ total_capacity |
| `f1_defer` | F1 de la clase diferir (índice canónico 0) frente a todo lo demás |
| `macro_f1` | media de las F1 de las cinco clases |
| `raw_assignment_accuracy` | exactitud vehículo a vehículo sobre el índice canónico |
| `confusion_matrix` | matriz sobre índices canónicos; fila = maestro, columna = predicción |
| `latency.mean_ms / median_ms / p99_ms` | tiempo del decodificador (`decode_episode`) por manifiesto |

Los cuatro últimos se calculan **después del decodificador**, sobre el plan que
se ejecutaría de verdad. Un argmax crudo sobre los logits mide otra cosa y no
entra a la misma tabla.

!!! warning "`f1_defer` y `macro_f1` no son intercambiables"
    La columna «F1 diferir» de la tabla comparativa se llenó durante meses con
    `f1_defer` para XGBoost, LightGBM y el transformer, y con **`macro_f1`** para
    el MLP, el Random Forest y la regresión logística. Nadie lo notó porque las
    dos son plausibles: `macro_f1` sale ~0,17 más alta porque promedia las cinco
    clases y las cuatro de camión —dos órdenes de magnitud más frecuentes—
    diluyen justo lo que se quería medir.

    Hoy `aggregate()` emite las dos y la tabla las publica en columnas
    separadas. Cualquiera de las dos se reconstruye desde la `confusion_matrix`
    que cada modelo publica en su JSON; que reconcilien está fijado por prueba
    (`tests/modeling/test_metrics.py`).

## Línea base

Cada modelo se reporta frente a la **línea base greedy**
(`src.modeling.metrics.evaluate_greedy`, primer ajuste por tamaño descendente),
que es la heurística manual que la entrega pide batir. La tabla de
[inicio](index.md) muestra que los seis modelos la superan por un margen
amplio en el objetivo primario.

## En MLflow

MLflow guarda las métricas como pares clave-valor planos, así que cada agregado
se registra **dos veces por modelo** —una para el modelo y otra para la línea
base greedy—, más las métricas de diagnóstico del clasificador. Esquema de
claves:

```
<modelo>_<model|greedy>_<agregado>       métricas operativas -- LO QUE SE PUBLICA
<modelo>_rawrow_accuracy                 diagnóstico: exactitud por fila de opción
<modelo>_rawrow_defer_f1                 diagnóstico: F1 de diferir por fila de opción
att_rawargmax_best_accuracy              diagnóstico: argmax crudo, mejor época
att_rawargmax_best_defer_f1              diagnóstico: ídem
att_cap_accuracy, att_cap_defer_f1       transformer, ya decodificado
```

Sólo el primer grupo entra a la tabla comparativa. Los demás son diagnósticos
del clasificador **antes** del decodificador y no son comparables con nada.

!!! warning "Las claves `att_*` cambiaron de nombre en agosto de 2026"
    Se llamaban `att_val_accuracy` y `att_val_defer_f1`, y la tabla comparativa
    las leía. Son un argmax crudo tomado en **la época que mejor puntuó en
    validación** —ni el decodificador, ni los pesos que se guardan—, así que el
    transformer aparecía como el modelo más exacto del cuadro con 0,857 cuando
    las otras cinco filas eran post-decodificador. Medido igual que las demás da
    0,830 y las seis quedan dentro de 0,02.

    El nombre lleva ahora escrito lo que es. Y `att_cap_*` reconcilia con
    `att_operational`, que antes no: `predict_with_capacity` fijaba
    `policy="model"` mientras el reporte operativo usaba la política elegida por
    validación, así que había **tres** mediciones distintas del mismo modelo.

Ejemplos: `xgb_model_optimality_gap_loaded_pct` es la brecha óptima de XGBoost;
`xgb_greedy_latency_mean_ms`, el tiempo medio de la línea base;
`att_model_capacity_violation_rate`, la puerta de factibilidad del transformer.

Cada `<agregado>` es exactamente la clave de la
[tabla de agregados](#agregados-aggregate), así que la UI de MLflow mapea 1:1
sobre las fórmulas de esta página. Las claves `latency_*` aparecen sueltas
(`_mean_ms`, `_median_ms`, `_p99_ms`, `_n_manifests_timed`), no anidadas.

Hay una sola base de datos, en la raíz del repositorio, compartida por el
pipeline Kedro y por `scripts/train_classical.py`:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

### Curvas de entrenamiento

**Los seis modelos dejan su curva versionada** en
`artifacts/<modelo>/training_history.csv` y `learning_curves.png`, con el formato
común de `src/modeling/figures.py`. Se regeneran sin reentrenar con
`just figures`.

!!! danger "Estuvieron sólo en MLflow, y se perdieron"
    Hasta agosto de 2026 el MLP era el único con la curva guardada; los otros
    cinco la registraban en MLflow y nada más. `mlflow.db` está en `.gitignore`,
    así que cuando la base se reinició los `run_id` de XGBoost, LightGBM y el
    transformer dejaron de resolver y **sus curvas dejaron de existir**: hubo que
    reentrenar para recuperarlas. Por eso ahora el archivo va junto al modelo, que
    sí se versiona, y MLflow queda como comodidad de la UI, no como el único sitio.

Cada modelo converge sobre un eje distinto, así que **la unidad viaja dentro del
CSV** en la columna `step_unit` y `plot_curves` rotula el eje leyéndola de ahí.
Rotular «época» una curva de XGBoost deja de ser posible por descuido:

| Modelo | `step_unit` | Series |
|---|---|---|
| MLP (Keras) | `epoch` | `loss`, `val_loss`, exactitud y su val |
| Transformer | `epoch` | `loss`, `val_loss`, exactitud, `val_defer_f1` |
| XGBoost | `boosting_round` | logloss y exactitud, train/val (500 rondas) |
| LightGBM | `boosting_round` | binary_logloss y exactitud, hasta la parada temprana |
| Random Forest | `n_trees` | log-loss y F1 macro, train/val |
| Regresión logística | `lbfgs_iter` | log-loss y F1 macro, train/val |

El Random Forest y la regresión logística no tienen «época»: su eje es el de su
propia convergencia —árboles añadidos e iteraciones de lbfgs—, que es el análogo
exacto de la ronda de boosting. Se obtienen con `warm_start`, así que producir la
curva **no cuesta un segundo ajuste**: el último tramo es el modelo publicado.

En MLflow las mismas series aparecen como `<modelo>_train_*` / `<modelo>_val_*`.
Los GBT las re-registran con esos nombres porque `autolog` usa las etiquetas del
propio framework y **los dos llaman «validation» a la partición de
entrenamiento**; el transformer añade `att_val_loss`, que antes no se calculaba.

### Matrices de confusión

**Las seis, en `artifacts/<modelo>/confusion_matrix.png` y sobre validación**,
que es la partición que publica la tabla comparativa y por tanto la única que se
puede poner una al lado de otra. El MLP guarda además
`confusion_matrix_test.png`: es su resultado final sobre 2026 y se publica igual,
pero con nombre propio, porque mezclarlo con las otras cinco sería repetir en
formato figura el error de juntar dos mediciones distintas.

Son **función pura de lo publicado**: `aggregate()` guarda `confusion_matrix` en
el JSON de los seis, así que redibujarlas nunca exige reentrenar.

```bash
just figures    # regenera las doce figuras desde los JSON y CSV guardados
```

Los índices son los canónicos (`0 = Sin camión`, `1..T` = camiones por capacidad
descendente) y las etiquetas son dinámicas: una por índice realmente presente,
nunca un número fijo.

!!! warning "Las del pipeline Kedro salían con los ejes corridos"
    `_confusion_matrix_figure` construía las etiquetas como
    `[Cam1..Camk] + ['Sin camión']`, pero el índice 0 **es** `Sin camión`. El
    resultado: la fila y la columna de diferir se rotulaban «Cam1», cada camión
    aparecía con el nombre del siguiente, y el más chico salía como «Sin camión».
    Todas las figuras del pipeline estuvieron mal etiquetadas hasta agosto de
    2026. El orden lo fija `canonicalization.py` y hoy lo construye
    `_etiquetas_canonicas`, una sola vez.

Dentro del pipeline Kedro, los nodos de entrenamiento sólo emiten predicciones
(`*_predictions.parquet`) y el nodo `report_confusion_matrices` dibuja a partir
de ellas —también en `fleet_loading/data/08_reporting/`, que está en
`.gitignore` y por eso no basta— y sobrescribe el `confusion_matrix.png` que
`mlflow.evaluate()` registra con etiquetas numéricas, localizándolo por el
`run_id` que cada modelo guarda en sus resultados.

```bash
cd fleet_loading && uv run --project .. kedro run --nodes report_confusion_matrices
```
