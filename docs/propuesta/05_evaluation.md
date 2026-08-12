# Evaluación

## Objetivo

Dado un manifiesto y su flota:

* **maximizar** vehículos transportados y aprovechamiento de CU;
* **minimizar** vehículos diferidos;
* que toda asignación sea **factible** bajo la restricción de capacidad.

El orden es lexicográfico estricto: primero cuántos vehículos se cargan y,
solo como desempate, cuánta capacidad se aprovecha. Es lo que optimiza el
maestro exacto.

**No se evalúa:** orden de la ruta ni kilómetros (fuera de alcance).

---

## Métricas

| Métrica | Qué mide |
|---|---|
| Exactitud de asignación | % de vehículos que coinciden con la etiqueta del maestro |
| Aprovechamiento de CU | CU cargada / CU disponible en la flota |
| Brecha de conteo | Vehículos que el maestro carga y el modelo no |
| Iguala al maestro | % de episodios donde el modelo carga tantos vehículos como el óptimo |
| Violación de capacidad | Debe ser **exactamente 0**; si no, el resto no significa nada |
| Tiempo de cómputo | ms por manifiesto |

Las definiciones exactas, con fórmula, están en
[métricas operativas](../metricas.md).

---

## Métodos comparados

| Método | Papel |
|---|---|
| Maestro exacto | Referencia óptima (programación dinámica, sin solvers externos) |
| Procedimiento actual | Agrupación regional al estilo humano |
| Greedy | Heurística de primer ajuste, la línea base a batir |
| **Los cuatro modelos** | MLP, XGBoost, LightGBM y transformer |

---

## Caso de estudio

Tarea diaria documentada: **18 vehículos**, **5 cantones**, **2 camiones** de
6 CU — ver [escenario](example/problem/scenario.md). Es un escenario de juguete
de la propuesta original, no la configuración con la que se entrena (1-4
camiones de 3,0-9,0 CU), pero sirve para verificar a mano que el maestro exacto
hace lo que dice.

En la [tabla comparativa](example/solution/comparisons.md), para este proyecto
importan **agrupación, carga en CU y vehículos en tierra**; las columnas de ruta
y distancia son ilustrativas.

| Caso | En tierra | Aprovechamiento |
|---|---|---|
| 1. Procedimiento actual | 6 vehículos | 5,0 / 6,0 CU por camión |
| 2. Greedy | 6 vehículos | 4,0 y 6,0 CU |
| 3. Carga óptima | 2 vehículos | 6,0 / 6,0 CU en ambos |

Páginas de detalle:
[procedimiento actual](example/problem/3_status_quo/status_quo.md) ·
[greedy](example/problem/2_greedy/greedy.md) ·
[óptimo](example/solution/4_optimized/optimized.md)

---

## Experimentos previstos

1. **Holdout temporal** — entrenar con 2018-2024, validar con 2025 (prueba: 2026).
2. **Barrido de tamaño** — N = 10, 20, 30, 50; greedy vs. modelo vs. búsqueda exhaustiva acotada.
3. **Réplica del caso de juguete** — que el etiquetador reproduzca la agrupación del caso 3.

---

## Resultados

Los experimentos se llevaron a cabo. Las cifras viven en las páginas que
reportan mediciones, no aquí:

- **Métricas operativas** y la tabla comparativa de modelos —
  [métricas operativas](../metricas.md) y [resultados](../modelo/resultados.md).
- **Holdout temporal** — implementado en `src/modeling/protocol.py` y compartido
  por los cuatro modelos. Su efecto medido frente a la partición aleatoria
  anterior está en
  [protocolo de partición](../decisiones/04_protocolo_de_particion.md).
- **Extrapolación más allá del tamaño de flota entrenado** (5-10 camiones) —
  [inicio](../index.md).

El experimento 1 dice 2018 y no 2017 como se planificó: el CSV de 2017 no trae
la columna `FECHA PROCESO`, así que no se puede situar en el tiempo y
`load_all_years` lo descarta.

El script que nombraba la propuesta original (`scripts/eval_loading.py`) nunca
se escribió. La evaluación la hacen `scripts/evaluate_mlp.py`,
`scripts/evaluate_fleet_loading.py` y el pipeline Kedro.
