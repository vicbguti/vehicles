# Pipeline Kedro

Entrena XGBoost, LightGBM y el transformer. El MLP va por su propio camino
(`scripts/train_mlp.py`), pero los cuatro comparten el núcleo de
`src/modeling`: los mismos tensores, el mismo decodificador y **la misma
partición**.

## Nodos

| Nodo | Entrada | Salida | Qué hace |
|---|---|---|---|
| `encode` | vehicles, episodes | encoded_vehicles | Une vehículos y episodios y conserva las columnas del maestro que necesitan los tensores por par (`truck_capacities`, `n_loaded`, `cu_utilized`), más `iso_year`, que es el eje de la partición temporal. Sin ingeniería de features: los modelos consumen los tensores canónicos de `src/modeling` |
| `split` | encoded_vehicles | train_df, val_df | Llama a `src.modeling.protocol.make_splits`: holdout temporal, descarte de episodios no óptimos y comprobación de que no hay fuga entre particiones |
| `train_xgboost` | train_df, val_df, episodes | xgb_results, xgb_predictions | Clasificador binario **por par** (una fila por opción `(vehículo, camión)` más la de diferir), decodificación con capacidad y métricas operativas |
| `train_lightgbm` | ídem | lgb_results, lgb_predictions | LightGBM con el mismo contrato |
| `train_attention` | ídem | att_results, att_predictions | Codificador transformer sobre el conjunto de vehículos del episodio, con cabeza por par y cabeza de diferimiento; eje de camiones dinámico |
| `report_confusion_matrices` | las tres predicciones + xgb/lgb_results | 5 figuras | Paso de puro renderizado: lee predicciones cacheadas y escribe los PNG |

Los nodos de entrenamiento solo emiten **datos** (métricas y predicciones) al
catálogo; nunca dibujan. Como las figuras son función pura de las predicciones,
recolorearlas es editar `_confusion_matrix_figure` en `nodes.py` y re-ejecutar
un solo nodo rápido:

```bash
kedro run --nodes report_confusion_matrices
```

No hace falta reentrenar.

## La partición es la misma para los cuatro modelos

`conf/base/parameters.yml`:

```yaml
split:
  train_years: [2018, 2019, 2020, 2021, 2022, 2023, 2024]
  val_years: [2025]
  test_years: [2026]
```

Antes este pipeline usaba `GroupShuffleSplit(test_size=0.2, random_state=42)`
mientras el MLP usaba holdout temporal, y **ambas cifras se publicaban en la
misma tabla**. El parámetro `test_size` ya no existe.

El efecto de ese cambio está medido, no supuesto: ver
[protocolo de partición](decisiones/04_protocolo_de_particion.md).

## El diseño por pares (por qué no hay número de camiones fijado)

Los tres modelos emiten logits por episodio `(V, 1 + T)` en el espacio de
índices canónico (`0 = SIN_CAMION`, `1..T` = camiones por capacidad
descendente) y se decodifican con `src.modeling.capacity_decoder.decode_episode`,
cuyo eje de camiones es `None`. Eso es lo que hace que funcionen con
**cualquier** número de camiones, incluidas las pruebas de extrapolación a 5-10.

La maquinaria compartida vive en `pipelines/training/pairwise.py`:

- `build_tensors` — `src.modeling.features.build_all_episodes` + `BlockScaler`
  (ajustado solo con entrenamiento) + `build_model_arrays`;
- `option_rows` / `logits_from_proba` — la vista de los GBT: un clasificador
  binario `is_chosen` sobre opciones `(vehículo, camión)` con una bandera
  explícita `is_defer`;
- `evaluate_split` / `select_policy` / `measure_latency` — elección de política
  del decodificador por `loaded_gap_mean` de validación, agregados por episodio
  contra el maestro y la línea base greedy, y latencia.

## Ejecutar

```bash
uv sync --extra gbt --extra attention --extra tracking --extra kedro
cd fleet_loading && uv run kedro run
```

No hay entorno virtual por subproyecto: hay un solo `pyproject.toml` y un solo
`uv.lock` en la raíz.

Los resultados van a `data/07_model_output/` y quedan registrados en MLflow. Los
modelos entrenados y sus esquemas de preprocesamiento se guardan además en
`artifacts/fleet_loading/<modelo>/` para el evaluador de extrapolación.

```bash
uv run --extra tracking mlflow ui --backend-store-uri sqlite:///mlflow.db
```
