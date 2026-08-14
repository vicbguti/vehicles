# Carga de flota

Asignación vehículo-camión por **aprendizaje supervisado por imitación**, a
partir del dataset de vehículos nuevos del SRI de Ecuador (2018-2026).

Dado un manifiesto —los vehículos matriculados en un cantón durante una semana—
y una flota de camiones con capacidades heterogéneas, hay que asignar cada
vehículo a un camión o diferirlo, sin exceder ninguna capacidad, maximizando en
este orden estricto: **cuántos vehículos se transportan** y, como desempate,
**cuánto espacio se aprovecha**.

El óptimo exacto lo calcula un buscador propio por programación dinámica
(`src/loading/labeler.py`, sin solvers externos), y ese óptimo es la etiqueta
con la que se entrenan cuatro modelos: un MLP en Keras, XGBoost, LightGBM y un
transformer en PyTorch.

## Los cuatro modelos comparten todo menos el modelo

Los cuatro son **por pares**: puntúan cada opción `(vehículo, camión)` más la
opción de diferir, produciendo logits `(V, 1 + T)` en el espacio canónico
(columna 0 = `SIN_CAMION`, 1..T = camiones por capacidad descendente), y
decodifican con un decodificador que respeta la capacidad. El eje de camiones es
completamente dinámico: **ningún modelo tiene un número de camiones codificado**.

Comparten los tensores de `src/modeling`, el decodificador, las métricas y —lo
que hace que sus cifras sean comparables entre sí— **la partición**
(`src/modeling/protocol.py`).

Todo plan producido es **factible por construcción**: un vehículo solo se coloca
si cabe en la capacidad restante. La tasa de violación de capacidad es 0 para
todos los modelos, y si alguna vez deja de serlo, el resto de las métricas no
significa nada.

## Resultados

Medido contra el maestro exacto sobre la validación del holdout temporal.

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

- **Brecha de conteo** = cuántos vehículos carga el maestro y el modelo no. Es
  la métrica que discrimina, porque el llenado en CU está acotado a ~36 %: los
  episodios son ricos en capacidad —sobra sitio en los camiones—, así que
  maestro y modelos convergen al mismo valor. Ver
  [cobertura de escenarios](propuesta/09_scenarios_coverage.md).
- **Latencia** es el tiempo del decodificador (`decode_episode`), el único paso
  que los modelos comparten; el ensamblado de los logits es específico de cada
  uno, y por eso el MLP no tiene fila aquí (ver la nota de la tabla).
- **Greedy** es la heurística de primer ajuste por tamaño descendente: la línea
  base a batir. Su brecha de conteo, **0,63 vehículos por episodio frente a
  ~0,03**, es la diferencia que justifica el proyecto entero.
- Los cuatro modelos rondan el **97 %** de episodios en los que igualan
  exactamente al maestro, contra el 87,4 % del greedy.

Las fórmulas exactas están en [métricas operativas](metricas.md).

### Extrapolación a flotas mayores

Los modelos se entrenan con 1-4 camiones. Evaluados sobre manifiestos
re-etiquetados con flotas más grandes (`scripts/evaluate_fleet_loading.py`),
donde `loaded_gap_mean` = media de (vehículos del maestro − vehículos del
modelo):

| Conjunto (camiones, capacidad) | XGBoost | LightGBM | Transformer | Greedy |
|---|---|---|---|---|
| 5-6, misma distribución | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| 8-10, capacidad total constante | 0,0274 | 0,0294 | 0,0209 | 0,0157 |

Con 5-6 camiones los tres igualan al maestro en el **100 %** de los episodios,
sin reentrenar. Es la comprobación de que la estructura por pares generaliza más
allá del rango visto en entrenamiento.

Agregados completos por modelo en
`artifacts/fleet_loading/<modelo>/extrap_*_metrics.json`.

## Puesta en marcha

Desde la raíz. No hace falta ningún entorno virtual por subproyecto: hay un solo
`pyproject.toml` y un solo `uv.lock`.

```bash
# 1. Entorno y datos. El paso de LFS no es opcional: sin él los CSV son
#    punteros de 133 bytes y el pipeline procesa basura en silencio.
uv sync
git lfs install --local && git lfs pull

# 2. Datos derivados (el barrido completo tarda ~30 min; --limit para muestrear)
uv run python scripts/build_vehicle_features.py
uv run python scripts/build_scenarios.py --limit 200

# 3. Entrenar y evaluar el MLP
uv run python scripts/train_mlp.py
uv run python scripts/evaluate_mlp.py

# 4. Los otros tres modelos (pipeline Kedro). Necesitan sus extras:
uv sync --extra gbt --extra attention --extra kedro
cd fleet_loading && uv run --project .. kedro run     # o: just train-fleet

# 5. MLflow (una sola base en la raíz, compartida por todos los entrenamientos)
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db

# 6. Documentación
uv run --extra docs mkdocs serve
```

Con [`just`](https://github.com/casey/just) instalado, `just setup` hace el paso
1 y deja los hooks de pre-commit activos. `just --list` muestra el resto.

## Por dónde seguir

| Si quieres… | Ve a |
|---|---|
| entender el problema | [la propuesta](propuesta/README.md) |
| ver el árbol del código | [estructura](estructura.md) |
| saber qué hay en `data/` | [datos](datos.md) |
| las fórmulas de las métricas | [métricas operativas](metricas.md) |
| por qué el repositorio está así | [decisiones de ingeniería](decisiones/01_hallazgos_transversales.md) |
| la trazabilidad al reporte IEEE | [entrega](entrega/index.md) |
