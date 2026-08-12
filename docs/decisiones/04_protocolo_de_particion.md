# Efecto medido del cambio de protocolo de partición

**Interno — sustenta la nota de §VI sobre el diseño de features.**

Complementa [`08_comparabilidad_cinco_modelos.md`](../decisiones/03_comparabilidad.md),
que planteó el problema sin llegar a medirlo.

## Qué se midió

Hasta la unificación convivían dos protocolos:

* MLP → holdout temporal (2018-2024 / 2025 / 2026);
* XGBoost, LightGBM y transformer → `GroupShuffleSplit(test_size=0.2, random_state=42)`.

Ambas cifras se publicaban en la misma tabla. La partición aleatoria dejaba **los
mismos 9 años y 172 de los 174 cantones** del conjunto de validación también en
entrenamiento. Como un episodio es (cantón, semana ISO), semanas contiguas del
mismo cantón son manifiestos casi gemelos.

`scripts/compare_split_protocols.py` entrena XGBoost dos veces sobre los mismos
534.680 registros, con los mismos hiperparámetros y la misma semilla, cambiando
únicamente la partición.

## Resultado

| Métrica (validación) | Aleatorio (viejo) | Temporal (nuevo) | Δ |
|---|---|---|---|
| Exactitud cruda | 0,7987 | **0,8098** | **+0,0111** |
| F1 macro | 0,7703 | **0,7758** | **+0,0055** |
| Iguala al maestro | 97,49 % | 96,92 % | **−0,57 pp** |
| Brecha de conteo (media) | 0,0258 | 0,0323 | +0,0065 (peor) |
| Violación de capacidad | 0,0000 | 0,0000 | — |
| *Greedy (control)* | *87,27 %* | *87,42 %* | *+0,15 pp* |

## Interpretación

**La fuga era real y casi no afectaba.** Dos métricas mejoran con la partición
honesta y la coincidencia con el maestro cae menos de un punto porcentual.

La razón no es casualidad: `src/modeling/features.py` excluye deliberadamente
`canton`, `uid`, `truck_id` y la posición del vehículo dentro de su clase,
argumentando en cada caso que sólo permiten memorizar. Cuando la partición
aleatoria puso 172 de 174 cantones a ambos lados, **no había identidad de
episodio que explotar**: el modelo sólo podía apoyarse en la aritmética de
capacidad, que generaliza igual de bien entre semanas que dentro de ellas.

Es decir, el diseño de features ya había neutralizado la fuga antes de que se
detectara. Merece una línea en §VI-A.

La fila del greedy es el control: es un algoritmo fijo, sin entrenamiento, así
que su variación (0,15 pp) mide cuánto difieren los dos conjuntos de validación
en dificultad intrínseca. Al ser mínima, las diferencias de los modelos son
efecto del protocolo y no de comparar episodios distintos.

## Límites de esta medición

* Los dos protocolos evalúan sobre **conjuntos distintos** (aleatorio ≈ 6.700
  episodios; temporal = 4.030, todo 2025). Compara protocolos, no las mismas
  instancias.
* Se usó `n_estimators=150` en vez de los 500 de producción, para que el A/B
  fuera ejecutable en minutos. Los **deltas** son sólidos; los valores absolutos
  son indicativos y no sustituyen a las cifras del reporte.
* Sólo se midió XGBoost. LightGBM debería comportarse igual (misma
  representación por filas de opción), pero el transformer es otra arquitectura
  y su delta no se puede extrapolar de aquí.

## Qué queda por hacer

Regenerar la tabla completa con un solo protocolo. No es reescribir §VII: las
conclusiones cualitativas se sostienen. Es volver a correrla para que las filas
sean comparables entre sí, que es lo que `assert_comparable`
(`src/modeling/protocol.py`) ahora exige.
