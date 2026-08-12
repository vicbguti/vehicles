# Métricas operativas

Los modelos se juzgan con las tres métricas formales de la entrega, calculadas
contra el **maestro exacto** de `data/episodes/episodes.parquet`, que lleva
`n_loaded` y `cu_utilized` por episodio (es decir, `V_exact` para cada
manifiesto).

Los cuatro modelos se evalúan sobre **la misma partición**: el holdout temporal
de `src/modeling/protocol.py` (entrenamiento 2018-2024, validación 2025, prueba
2026). La maquinaria es `src/modeling/metrics.py`, la misma que evalúa el MLP,
a través de `fleet_loading/src/fleet_loading/pipelines/training/pairwise.py`.

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
| Modelo | Exactitud | F1 diferir | Brecha de conteo | Iguala al maestro | Llenado (CU) | Violación cap. | Latencia media / p99 (ms) |
|---|---|---|---|---|---|---|---|
| **XGBoost** | 0,826 | 0,618 | 0,0288 | 97,2 % | 35,6 % | 0,0 | 0,04 / 0,07 |
| **LightGBM** | 0,825 | 0,616 | 0,0268 | 97,4 % | 35,6 % | 0,0 | 0,04 / 0,07 |
| **Transformer** | 0,857 | 0,699 | 0,0318 | 97,0 % | 35,5 % | 0,0 | 0,04 / 0,06 |
| **MLP (Keras)** | 0,829 | 0,796 | 0,0266 | 97,4 % | 35,6 % | 0,0 | — / — |
| **Greedy (línea base)** | — | — | 0,6310 | 87,4 % | 36,2 % | 0,0 | 0,04 / 0,07 |

Medido sobre la validación del protocolo temporal (**4030 episodios**, año 2025) contra el maestro exacto.

La **latencia del MLP se omite a propósito**: `scripts/evaluate_mlp.py` cronometra la inferencia completa (`model.predict` + decodificación, ~43 ms, dominada por la sobrecarga de Keras), mientras que el pipeline Kedro cronometra solo `decode_episode` (~0,04 ms). Son dos mediciones distintas y ponerlas en la misma columna las haría parecer comparables.

Tabla generada por `scripts/report_model_table.py` a partir de los JSON medidos. **No editar a mano**: se regenera, y `--check` lo verifica en CI.
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
| `latency.mean_ms / median_ms / p99_ms` | tiempo del decodificador (`decode_episode`) por manifiesto |

## Línea base

Cada modelo se reporta frente a la **línea base greedy**
(`src.modeling.metrics.evaluate_greedy`, primer ajuste por tamaño descendente),
que es la heurística manual que la entrega pide batir. La tabla de
[inicio](index.md) muestra que los cuatro modelos la superan por un margen
amplio en el objetivo primario.

## En MLflow

MLflow guarda las métricas como pares clave-valor planos, así que cada agregado
se registra **dos veces por modelo** —una para el modelo y otra para la línea
base greedy—, más las métricas de diagnóstico del clasificador. Esquema de
claves:

```
<modelo>_<model|greedy>_<agregado>       métricas operativas
<modelo>_val_accuracy                    exactitud sobre la etiqueta cruda (diagnóstico)
<modelo>_val_defer_f1                    F1 de diferir sobre la etiqueta cruda (diagnóstico)
att_cap_accuracy, att_cap_defer_f1       transformer, decodificador con capacidad
```

Ejemplos: `xgb_model_optimality_gap_loaded_pct` es la brecha óptima de XGBoost;
`xgb_greedy_latency_mean_ms`, el tiempo medio de la línea base;
`att_model_capacity_violation_rate`, la puerta de factibilidad del transformer.

Cada `<agregado>` es exactamente la clave de la
[tabla de agregados](#agregados-aggregate), así que la UI de MLflow mapea 1:1
sobre las fórmulas de esta página. Las claves `latency_*` aparecen sueltas
(`_mean_ms`, `_median_ms`, `_p99_ms`, `_n_manifests_timed`), no anidadas.

La base de datos la escribe el pipeline en `fleet_loading/mlflow.db`:

```bash
uv run --extra tracking mlflow ui --backend-store-uri sqlite:///fleet_loading/mlflow.db
```

### Curvas de entrenamiento

Las curvas se registran de forma nativa y la UI de MLflow las dibuja como
gráficos de línea. Los GBT además re-registran las suyas con nombres sin
ambigüedad, porque `autolog` usa las etiquetas del propio framework y **los dos
llaman «validation» a la partición de entrenamiento**:

- **XGBoost**: `xgb_train_logloss` / `xgb_train_accuracy_curve` (entrenamiento),
  `xgb_val_logloss` / `xgb_val_accuracy_curve` (validación) — un paso por ronda
  de boosting (500). Las `validation_0/1-logloss` de autolog son los mismos
  datos con la nomenclatura de XGBoost.
- **LightGBM**: `lgb_train_binary_logloss` / `lgb_train_accuracy_curve`,
  `lgb_val_binary_logloss` / `lgb_val_accuracy_curve` — un paso por ronda hasta
  la parada temprana.
- **Transformer**: `att_train_loss` / `att_train_accuracy_curve`,
  `att_val_accuracy_curve`, `att_val_defer_f1_curve` — un paso por época (50).

Salen de `mlflow.<framework>.autolog(log_models=False)`, que captura los
resultados nativos del `eval_set`, más un `mlflow.log_metric(..., step=epoch)`
por época.

### Matrices de confusión

Las matrices de confusión **no** se producen durante el entrenamiento. Los nodos
de entrenamiento solo emiten predicciones (`*_predictions.parquet`); el nodo
`report_confusion_matrices` dibuja las figuras a partir de ellas en
`fleet_loading/data/08_reporting/`.

Los tres modelos emiten predicciones en el espacio de índices canónico
(`0 = Sin camión`, `1..T` = camiones por capacidad descendente), así que las
matrices son de `(T+1)` vías con **etiquetas dinámicas**: una columna por índice
de camión realmente presente, nunca un número fijo.

| Figura | Fuente de predicciones |
|---|---|
| `xgb_confusion_matrix_train.png`, `xgb_confusion_matrix_val.png` | `xgb_predictions.parquet` |
| `lgb_confusion_matrix_train.png`, `lgb_confusion_matrix_val.png` | `lgb_predictions.parquet` |
| `att_confusion_matrix_val.png` (decodificador con capacidad) | `att_predictions.parquet` |

Como las figuras son función pura de `(y_true, y_pred, labels)`, recolorearlas
nunca exige reentrenar: se edita `_confusion_matrix_figure` en `nodes.py` y se
re-ejecuta un solo nodo.

```bash
cd fleet_loading && uv run --project .. kedro run --nodes report_confusion_matrices
```

Ese nodo además sobrescribe el artefacto `confusion_matrix.png` que registra
`mlflow.evaluate()` con etiquetas numéricas: MLflow necesita clases numéricas
para calcular su matriz, así que el entrenamiento deja intacta su versión y el
nodo de reporte la reemplaza por una legible y normalizada, en la misma
ejecución, localizada por el `run_id` que guarda cada modelo en sus resultados.
