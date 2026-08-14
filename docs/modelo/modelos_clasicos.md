# Modelos clásicos: Random Forest y regresión logística

Los otros cuatro modelos —MLP, XGBoost, LightGBM y el transformer— son **por
pares**: puntúan cada opción `(vehículo, camión)` y dejan el eje de camiones
abierto, así que aceptan cualquier tamaño de flota en inferencia.

`RandomForestClassifier` y `LogisticRegression` no pueden hacer eso. Son
clasificadores de `K` clases fijas: reciben una `X` de ancho constante y
predicen un único índice entre `0..K-1`. No hay forma de darles un eje
dinámico sin dejar de usarlos como lo que son.

La formulación que sí les corresponde está en
[`src/modeling/flat_features.py`](https://github.com/vicbguti/vehicles/blob/main/src/modeling/flat_features.py):
**rellenar la flota a un tamaño fijo** y tratar cada posición canónica como una
columna de features más, en vez de un eje del modelo.

## Qué se gana y qué se pierde

**Se pierde generalización a flotas grandes.** Con relleno a `max_trucks`, el
modelo no sabe nada de un episodio con más camiones que ese tope, y
`build_flat_arrays` lanza `ValueError` en vez de truncar en silencio.

Esa limitación **no afecta a este dataset**, y no por casualidad:
`N_TRUCKS_RANGE = (1, 4)` en `src/loading/scenarios.py` fija el tope en el
propio generador de escenarios, así que ningún episodio —entrenamiento,
validación o prueba— lo excede. Es una restricción conocida y acotada, no un
descuido.

**No se pierde comparabilidad**, que es lo que importa para la tabla. El
objetivo (`canonical_target_index`) es el mismo: `0 = SIN_CAMION`, `1..T` el
camión canónico por capacidad descendente, ver
[canonicalización](canonicalizacion.md). Y las métricas de dominio salen de
`src.modeling.metrics.aggregate`, decodificando con
`capacity_decoder.decode_episode` — **el mismo código que usan los otros
cuatro**. No hay una segunda implementación de las métricas.

## Una salvaguarda que conviene conocer

`predict_proba` solo devuelve columnas para las clases que el modelo vio en
entrenamiento (`model.classes_`). Si alguna faltara —por ejemplo, si ningún
vehículo hubiera ido nunca al camión más chico de una flota de cuatro—, esas
columnas quedarían **desalineadas** con el índice canónico que espera el
decodificador, y el modelo se evaluaría mal sin que nada fallara.

`scripts/train_classical.py` compara `model.classes_` contra
`np.arange(max_trucks + 1)` y aborta si no coinciden.

## Búsqueda de hiperparámetros

Con [Optuna](https://optuna.org) (`TPESampler`, semilla fija), maximizando F1
macro en validación. Cada intento queda registrado como un run anidado en
MLflow, en la misma base que el resto de los modelos.

Dos detalles de la búsqueda de la regresión logística:

* Es **condicional**: `lbfgs` solo admite L2 puro, así que `l1_ratio` únicamente
  se sugiere cuando el solver es `saga`. Por eso el mejor conjunto de
  hiperparámetros se recompone con `finalize_params` — `study.best_params` no
  trae las claves que Optuna no llegó a sugerir en ese intento.
* Se usa `l1_ratio`, no `penalty`. Desde scikit-learn 1.8, pasar `penalty="l1"`
  junto al `l1_ratio=0.0` por defecto emite un `UserWarning` de valores
  inconsistentes y **no aplica L1**. Y `multi_class="multinomial"` se eliminó en
  1.7: con estos solvers la pérdida ya es multinomial por defecto.

## Cómo se entrenan

```bash
just train-rf          # o: uv run python scripts/train_classical.py --model rf
just train-logreg
```

Cada uno deja en `artifacts/<modelo>/`: `model.joblib`, `feature_schema.json`
—con el `BlockScaler` y los nombres de columna—, `label_mapping.json` y
`training_report.json`, que es de donde
[la tabla comparativa](../index.md) toma las cifras.

`training_report.json` guarda `split_strategy`, y
`scripts/report_model_table.py` **rechaza publicar** una fila que no se haya
medido con la partición temporal. Es la misma puerta que se aplica al MLP, y
existe porque publicar cifras de protocolos distintos en una misma tabla es
justo el error que este repositorio ya cometió una vez.
