# La tabla comparativa de los cinco modelos no era construible

!!! success "Estado: resuelto"
    Este documento diagnosticó el problema el 6 de agosto de 2026. Desde
    entonces se aplicaron los tres arreglos y **la divergencia ya no existe**:

    * **Partición** — los cuatro modelos comparten
      `src/modeling/protocol.py`; `assert_comparable` falla si alguien intenta
      publicar en la misma tabla cifras medidas con protocolos distintos. El
      efecto está medido en
      [protocolo de partición](04_protocolo_de_particion.md).
    * **Rutas absolutas del catálogo** — `conf/base/catalog.yml` usa rutas
      relativas; `kedro run` ya no depende de la máquina de nadie.
    * **Dependencias no declaradas** — `xgboost`, `lightgbm`, `mlflow` y
      `torch` son extras declarados en `pyproject.toml`.

    Se conserva porque explica **por qué** el repositorio está organizado como
    está, y porque el diagnóstico sigue siendo la justificación de esas tres
    piezas. Lo que se lee abajo describe el estado de entonces.

> **Interno — no va al reporte.** Para Víctor y Nicolás.
>
> En [`05_hallazgos_para_el_equipo.md`](../decisiones/01_hallazgos_transversales.md) §7, la consolidación de
> los cinco modelos en una tabla comparable figura como **«sin dueño»**. Revisando el
> repositorio completo antes de subir mi trabajo, resulta que el problema no es que falte
> quien la escriba: es que hoy **no hay dos modelos que estén midiendo lo mismo**, así que
> cualquier tabla que armemos ahora compararía números que no son comparables.

Esto no es una crítica al trabajo de nadie. Los dos lados se desarrollaron en paralelo y cada
uno tomó decisiones razonables por separado. Pero hay que reconciliarlas antes de la §VII, y
cuanto antes mejor, porque afecta a las cifras que reportemos.

---

## 1. Las tres divergencias

| | `src/modeling/` (MLP) | `fleet_loading/` (XGBoost, LightGBM, atención) |
|---|---|---|
| **Partición** | Temporal: train 2018-24, val 2025, test 2026 (`src/modeling/dataset.py`, `split_by_time`) | `GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)` agrupando por `episode_id` (`nodes.py:143-147`) |
| **Métricas** | Operativas, por episodio: violación de capacidad, brecha de vehículos cargados, % que iguala el óptimo, CU aprovechada (`src/modeling/metrics.py`) | `accuracy_score` y `f1_score(pos_label=False)`, por fila (`nodes.py:214-218`, `282-286`) |
| **Etiqueta** | Canonicalizada por capacidad descendente (`src/modeling/canonicalization.py`) | `CAMION_k` cruda, en el orden aleatorio del generador |

Las tres son independientes: arreglar una no arregla las otras.

**La partición.** `GroupShuffleSplit` reparte episodios al azar entre train y test, así que
episodios de 2026 entran al entrenamiento. La partición temporal no. Un modelo evaluado con la
primera tiene una tarea más fácil que uno evaluado con la segunda, y la diferencia no es
pequeña ni acotable a ojo. Ambos agrupan por `episode_id`, así que ninguno tiene fuga
vehículo-a-vehículo — el problema es solo cuál conjunto es el de prueba.

**Las métricas.** Ésta es la divergencia de fondo. La exactitud por fila responde «¿acerté el
nombre del camión?»; las métricas operativas responden «¿cuántos vehículos transporté y me
pasé de capacidad?». En este problema **no están correlacionadas**: en mis mediciones, el greedy
tiene exactitud 0,4928 y el MLP 0,5297 (una diferencia menor), pero en brecha de vehículos
cargados el greedy da +0,5990 y el MLP +0,0229 — un factor de 26. Un modelo puede ganar en
exactitud y perder en lo que le importa al operador. Si la tabla de la §VII se llena con
exactitudes, mide lo que no decidimos optimizar.

**La etiqueta.** Documentada en detalle en
[`06_canonicalizacion_y_etiquetado.md`](../modelo/canonicalizacion.md). Sin canonicalizar,
`CAMION_1` no significa «el camión grande» sino «el que salió primero del generador», y el
0,26 % de soporte de `CAMION_4` hace que ningún modelo lo aprenda. Dos modelos medidos contra
convenciones de etiqueta distintas no son comparables ni siquiera en exactitud.

---

## 2. Dos problemas operativos, aparte

**`kedro run` no arranca fuera de la máquina de Víctor.**
`fleet_loading/conf/base/catalog.yml:1-7` usa rutas absolutas:

```yaml
vehicles:
  filepath: /home/vicbguti/Projects/vehicles/data/episodes/episode_vehicles.parquet
episodes:
  filepath: /home/vicbguti/Projects/vehicles/data/episodes/episodes.parquet
```

Con rutas relativas al proyecto Kedro, cualquiera del equipo podría reproducir esos modelos —
hoy no. Y va a hacer falta, porque tras el parche de orden de flota hay que reentrenar.

**Cuatro dependencias duras no están declaradas.** `nodes.py` y `attention_model.py` importan
`xgboost`, `lightgbm`, `mlflow` y `torch`, y ninguna aparece en `requirements.txt`, en
`pyproject.toml` ni en `fleet_loading/pyproject.toml` (que solo declara `kedro`, `ipython`,
`jupyterlab` y `notebook`). El entorno que funciona hoy depende de instalaciones manuales que
nadie más puede reconstruir.

---

## 3. Lo que propongo

No lo implementé porque toca código de ustedes dos, y porque la decisión de qué métricas manda
es del grupo, no mía. Pero el trabajo que ya está hecho cubre la mayor parte:

1. **Partición**: que `fleet_loading` llame a `src/modeling/dataset.py::split_by_time` en vez de
   `GroupShuffleSplit`. Trae `assert_no_episode_leakage()` de regalo.
2. **Métricas**: que los tres modelos de Kedro produzcan una matriz de puntuaciones
   vehículo × camión y la pasen por `src/modeling/capacity_decoder.py` y luego por
   `src/modeling/metrics.py`. **El decodificador es agnóstico del modelo a propósito** — opera
   sobre cualquier matriz de puntuaciones, no sabe si vino de un MLP o de un GBT. Es integración,
   no reescritura.
3. **Etiqueta**: `canonicalize_fleet(row["truck_capacities"])` antes de entrenar. Tres líneas,
   Python puro, sin dependencias. **Si canonicalizan la etiqueta, canonicalicen también las
   features de capacidad**: si tienen `cap_1..cap_4` en el orden del parquet y la etiqueta
   remapeada, la correspondencia se rompe y queda peor que antes. Usen el objeto `fleet` entero.
4. **Rutas**: relativas en `catalog.yml`.
5. **Dependencias**: declarar las cuatro que faltan.

Los puntos 1–3 son los que hacen que la tabla de la §VII signifique algo. Con ellos, las
columnas «violación de capacidad», «brecha de vehículos cargados» y «% que iguala el óptimo»
salen de la misma función para los cinco modelos, y la comparación es de verdad.

Si prefieren dejar la exactitud por fila como columna adicional, perfecto — pero entonces hay
que reportarla contra el techo (0,9243, ver `06_` §5), porque en crudo no dice nada.

---

## 4. Orden sugerido

El parche de orden de flota obliga a reentrenar de todos modos, así que conviene aprovechar ese
reentrenamiento para hacer también los puntos 1–3 y no reentrenar dos veces:

1. Se mergea el parche de `scenarios.py` y se regenera el dataset (~8 min).
2. Antes de reentrenar, se aplican partición, métricas y canonicalización comunes.
3. Cada quien reentrena una sola vez, ya midiendo lo mismo.
4. Se llena la §VII.
