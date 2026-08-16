# Resultados preliminares — Modelo MLP

> **Aporte de Juan Francisco Fernández Ramos a la sección VII del reporte.**
> Cubre únicamente el MLP; los resultados de los otros cuatro modelos y su
> consolidación en una tabla comparable siguen sin dueño asignado (ver
> `05_hallazgos_para_el_equipo.md`, y `08_comparabilidad_cinco_modelos.md` para por qué esa
> tabla hoy no se puede construir).
>
> Toda cifra de este documento proviene de `artifacts/mlp/metrics.json`,
> `artifacts/mlp/training_report.json`, `artifacts/mlp/label_ceilings.json`,
> `artifacts/mlp/teacher_self_agreement.json`, los `artifacts/mlp/metrics_extrap_*.json`
> (§6) o las tablas de episodios bajo `data/episodes/` (coste del maestro, §6.2). No hay
> valores estimados ni proyectados.

> **Medido sobre el conjunto con la flota ordenada.** El 27 de julio se documentó que el
> generador de escenarios devolvía las capacidades en orden aleatorio, que eso determinaba
> cuál de los planes óptimos empatados producía el etiquetador, y que esa información no
> estaba entre las entradas del modelo. El grupo acordó corregirlo: `generate_fleet()` ahora
> ordena la flota, el conjunto se regeneró y el modelo se reentrenó con los **mismos
> hiper-parámetros y la misma semilla**. Todas las cifras de aquí en adelante son
> posteriores a ese cambio. El análisis que llevó a la decisión está en
> [`06_canonicalizacion_y_etiquetado.md`](../modelo/canonicalizacion.md).

---

## 1. Conjunto de datos utilizado

Generado con `scripts/build_scenarios.py` sobre los 2.491.511 vehículos en alcance del
conjunto del SRI:

| | |
|---|---:|
| Grupos cantón-semana totales | 55.076 |
| Excluidos por el piso N<5 | 20.237 |
| Episodios construidos y etiquetados | **34.839** |
| Filas vehículo-episodio | **534.680** |
| Episodios donde el etiquetador no probó optimalidad | **0** |
| Episodios triviales (ningún vehículo diferido) | 29.860 (85,7 %) |
| Vehículos diferidos | 22.653 (4,24 %) |

> **Corrección respecto a la sección VI-A.** El reporte estima *"35 mil × 13 = 455 mil
> ejemplos"*. El valor medido es **534.680**. Del mismo modo, la sección VI-A supone que
> `SIN CAMIÓN` está unas 33 veces subrepresentada; el desbalance medido es de **22,6 a 1**
> (4,24 % de las filas).

Partición temporal por episodio completo — entrenamiento 2018-2024 (29.278 episodios,
444.051 filas), validación 2025 (4.030 / 66.399), prueba 2026 (1.531 / 24.230).

Ordenar la flota **no altera ninguna de estas cifras**: el número de episodios, de filas, de
triviales y de no-óptimos es idéntico al del conjunto anterior, porque ordenar no consume
aleatoriedad. Lo único que cambia es qué camión concreto recibe cada vehículo.

Lo que sí cambia es el reparto de la etiqueta, que era el problema:

| Etiqueta canónica (entrenamiento) | Antes | Ahora |
|---|---:|---:|
| `SIN CAMIÓN` | 4,26 % | 4,26 % |
| `CAMIÓN 1` (mayor capacidad) | 52,29 % | 31,07 % |
| `CAMIÓN 2` | 25,33 % | 25,80 % |
| `CAMIÓN 3` | 13,16 % | 23,04 % |
| `CAMIÓN 4` (menor capacidad) | **4,97 %** | **15,84 %** |

La columna «antes» ya está canonicalizada; sobre la etiqueta cruda `CAMIÓN 4` tenía apenas
**0,26 %** de soporte. Es decir, la canonicalización aguas abajo subía ese soporte de 0,26 %
a 4,97 %, y ordenar la flota en el generador lo lleva a 15,84 %. Con 0,26 % ningún modelo
aprende esa clase; con 4,97 % la aprende mal; con 15,84 % la aprende.

---

## 2. Entrenamiento

| | |
|---|---:|
| Parámetros del modelo | 4.482 |
| Épocas ejecutadas (máximo 100) | 51 |
| Mejor época, por pérdida de validación | 41 |
| Tiempo de entrenamiento (CPU) | 123,0 s |
| Pérdida de validación en la mejor época | 0,4757 |
| Reducciones automáticas de la tasa de aprendizaje | 6 (de 1e-3 a 1,6e-5) |

La parada temprana se activó en la época 51 y restauró los pesos de la 41. Curvas en
`artifacts/mlp/learning_curves.png`, historial completo en `training_history.csv`.

### 2.1 Sobre la separación aparente entre las curvas

En la figura de curvas de aprendizaje, la pérdida de entrenamiento (≈0,32) queda por debajo
de la de validación (≈0,48). **Esa separación no es sobreajuste**: el entrenamiento aplica
pesos de clase para compensar el desbalance de `SIN CAMIÓN` y la validación no, de modo que
las dos series no están en la misma escala. Evaluando las tres particiones con el mismo
criterio, sin pesos:

| Partición | Pérdida sin pesos | Exactitud |
|---|---:|---:|
| Entrenamiento | 0,4939 | 0,8146 |
| Validación | **0,4757** | 0,8266 |
| Prueba | **0,4323** | 0,8497 |

Medidas de forma comparable, la pérdida de validación y la de prueba resultan **menores** que
la de entrenamiento, y la exactitud es mayor. No hay sobreajuste: con 4.482 parámetros frente
a 444.051 filas de entrenamiento, el modelo está limitado por la señal disponible, no por su
capacidad. Las cifras quedan registradas en `artifacts/mlp/training_report.json` bajo
`unweighted_loss`.

---

## 3. Resultados sobre la partición de prueba (2026)

Métricas en orden de relevancia para el dominio. La comparación es contra el **etiquetador
exacto**, que resuelve el mismo problema de forma óptima y sirve de referencia.

| Métrica | MLP + decodificador | Greedy (primer ajuste) | Etiquetador exacto |
|---|---:|---:|---:|
| **1. Tasa de violación de capacidad** | **0,0000** | 0,0000 | 0 |
| **2. Brecha de vehículos cargados** (media) | **+0,0242** | +0,5990 | 0 |
| Brecha máxima en un episodio | 1 | 13 | 0 |
| Episodios que igualan el conteo óptimo | **97,58 %** | 87,98 % | 100 % |
| Brecha de optimalidad relativa | **0,15 %** | 4,17 % | 0 % |
| **3. Brecha de CU aprovechada** (media) | +0,0760 | **+0,0007** | 0 |
| Utilización de la capacidad | 32,71 % | 33,22 % | 33,22 % |
| **4. Vehículos diferidos** | 1.037 | 1.917 | 1.000 |
| **5. F1 macro** | **0,8131** | 0,1830 | — |
| Concordancia por clase | **0,9293** | 0,2850 | — |
| Planes idénticos al óptimo | **76,75 %** | 16,92 % | 100 % |
| **6. Latencia por manifiesto** (media / p99) | 43,1 / 55,9 ms | — | 10,2 ms † |
| **7. Exactitud cruda de asignación** | **0,8458** | 0,2683 | — |

† La latencia del etiquetador exacto es su `search_time_ms` medio durante la regeneración del
conjunto, no una medición de `metrics.json`. Conviene leerla con cautela: es tiempo de
búsqueda puro, sin la sobrecarga de una llamada de inferencia, y ambas cifras se midieron en
la misma máquina pero no en el mismo proceso. La latencia del modelo, además, varía entre
corridas (33 a 43 ms) porque está dominada por esa sobrecarga y no por el cómputo.

**Lo que sí se consiguió.** El plan entregado nunca excede la capacidad de un camión, en
ninguna de las tres particiones y en ningún episodio. Sobre el objetivo primario del
problema —cuántos vehículos se transportan— el modelo iguala la solución óptima en el
97,58 % de los episodios y deja una brecha media de 0,024 vehículos por manifiesto, frente a
0,599 de la heurística greedy: una reducción de **25 veces**. Y reproduce el plan completo
del etiquetador, camión por camión, en el 76,75 % de los episodios.

**Lo que no se consiguió.** El greedy aprovecha *más* capacidad (brecha de CU +0,0007 frente
a +0,0760). No es contradictorio: el greedy carga primero los vehículos voluminosos, así que
transporta menos unidades pero llena más espacio. Bajo el objetivo lexicográfico del
problema —primero cantidad, después aprovechamiento— el modelo gana; bajo el aprovechamiento
aislado, pierde.

> **Nota al comparar con la versión anterior de esta tabla.** Las métricas *operativas* del
> greedy son idénticas a las de antes del cambio, hasta el último decimal: brecha de conteo
> +0,5990, 87,98 % de episodios óptimos, brecha de CU +0,0007, 1.917 diferidos. Eso confirma
> que ordenar la flota no alteró el problema. Sus métricas de *clasificación*, en cambio,
> bajaron (F1 macro de 0,2421 a 0,1830; exactitud de 0,4928 a 0,2683), y eso es esperado: el
> greedy nunca intentó reproducir el reparto del etiquetador, y antes acertaba por accidente
> porque casi todo era `CAMIÓN 1`. Con la etiqueta equilibrada, ese acierto accidental
> desaparece. Es un argumento más para no reportar exactitud cruda sin su techo.

---

## 4. Selección de la política del decodificador

Elegida sobre validación (2025) por brecha de conteo, nunca sobre prueba:

| Política | Brecha de conteo | Brecha de CU | Violaciones |
|---|---:|---:|---:|
| **`model`** — orden por margen del modelo | **+0,0266** | +0,0794 | 0,0000 |
| `count` — orden por CU ascendente | +0,0333 | +0,1038 | 0,0000 |
| `respect_defer` — honra el `SIN CAMIÓN` predicho | +1,0166 | +0,8620 | 0,0000 |

El resultado más informativo es el tercero: **honrar el `SIN CAMIÓN` predicho degrada la
brecha de conteo en un factor de 38**. Confirma experimentalmente la decisión de diseño de
que el decodificador no difiera voluntariamente un vehículo que cabe, dado que el objetivo
primario es maximizar la cantidad transportada.

---

## 5. Análisis crítico: dónde aporta el modelo y dónde no

### 5.1 Ablación — ¿aporta el MLP, o basta el decodificador?

Se sustituyeron las puntuaciones del modelo por logits nulos, dejando actuar sólo al
decodificador, sobre los mismos 1.531 episodios de prueba
(`scripts/evaluate_mlp.py`, bloque `ablation_null_logits`):

| Configuración | Brecha de conteo | Iguala el óptimo | Brecha de CU | Concordancia por clase |
|---|---:|---:|---:|---:|
| MLP + decodificador | **+0,0242** | **97,58 %** | +0,0760 | **0,9293** |
| Logits nulos + decodificador | +0,2371 | 90,66 % | **+0,0267** | 0,3092 |

**Conclusión, y corrige a la versión anterior de este documento.** El aporte del MLP es real
y ahora se ve en **las dos dimensiones**: reduce la brecha de conteo casi diez veces y sube
el porcentaje de episodios óptimos del 90,66 % al 97,58 %, *y además* triplica la
concordancia por clase (0,3092 → 0,9293).

Antes del cambio en el generador, esta misma ablación mostraba que el modelo **no aportaba
nada** a la elección de camión: 0,5507 con modelo frente a 0,5469 sin él. Esa conclusión era
correcta sobre aquel conjunto y es falsa sobre éste. No era que el modelo no pudiera aprender
a elegir camión: era que sobre aquellas etiquetas no había nada aprendible que elegir.

### 5.2 Matriz de confusión — el colapso desapareció

Cobertura por etiqueta canónica sobre el plan decodificado:

| Etiqueta | Aciertos / total | Cobertura | Antes |
|---|---:|---:|---:|
| `SIN CAMIÓN` | 647 / 1.000 | 64,7 % | 64,2 % |
| `CAMIÓN 1` (mayor capacidad) | 6.529 / 7.247 | 90,1 % | 90,7 % |
| `CAMIÓN 2` | 5.243 / 6.458 | 81,2 % | 10,0 % |
| `CAMIÓN 3` | 4.481 / 5.405 | 82,9 % | 1,7 % |
| `CAMIÓN 4` (menor capacidad) | 3.594 / 4.120 | **87,2 %** | **0,0 %** |

La política aprendida ya no es *«al camión de mayor capacidad mientras quepa»*. El modelo
reparte entre los cuatro camiones con cobertura entre el 81 % y el 90 %, y `CAMIÓN 4` —que
antes no se predecía nunca— se acierta en el 87,2 % de los casos. El F1 macro sube de 0,2996
a 0,8131 en consecuencia.

La clase que peor se resuelve es `SIN CAMIÓN` (64,7 %), y es la que cabe esperar: decidir que
un vehículo **no** viaja depende de la ocupación acumulada del resto del manifiesto, no de
las features del vehículo.

### 5.3 El modelo es insensible a los hiper-parámetros dentro del ruido

Ocho configuraciones entrenadas y evaluadas de punta a punta
(`scripts/sweep_mlp.py`, resumen en `artifacts/mlp/sweep/summary.json`), ordenadas por brecha
de conteo sobre validación:

| Configuración | Parámetros | Brecha de conteo (val) | Brecha de CU (val) | Iguala el óptimo (prueba) |
|---|---:|---:|---:|---:|
| `batch_512` | 4.482 | **0,0241** | 0,0765 | 97,65 % |
| `dropout_030` | 4.482 | 0,0256 | 0,0813 | 97,52 % |
| `lr_3e-4` | 4.482 | 0,0258 | 0,0800 | **97,84 %** |
| **`base_64_32`** (adoptada) | 4.482 | 0,0266 | 0,0794 | 97,58 % |
| `dropout_010` | 4.482 | 0,0270 | 0,0788 | 97,45 % |
| `lr_3e-3` | 4.482 | 0,0278 | 0,0810 | 97,39 % |
| `ancha_128_64_32` | 16.130 | 0,0280 | 0,0817 | 97,58 % |
| `ancha_dropout_010` | 14.018 | 0,0313 | 0,0803 | 97,32 % |

Las ocho caben en una franja de **0,0072 vehículos por manifiesto**, y ninguna viola
capacidad. La configuración adoptada queda cuarta, a 0,0025 de la mejor — una diferencia sin
consecuencia operativa: sobre 1.531 episodios de prueba, todas las configuraciones igualan el
conteo óptimo entre el 97,3 % y el 97,8 % de las veces.

El resultado que importa es el de las dos últimas filas: **las variantes anchas, con 3,1 y
3,6 veces más parámetros, quedan en los dos últimos puestos.** Añadir capacidad no ayuda. El
factor limitante no es el tamaño del modelo ni la elección de hiper-parámetros, sino la señal
disponible en la etiqueta — que es lo que mide la sección 5.5.

> La prueba de significancia emparejada que acompañaba a esta tabla en la versión anterior
> (t = 1,51 sobre las diferencias por episodio) **no se repitió** sobre este conjunto, porque
> requiere las predicciones episodio a episodio de dos modelos y el barrido sólo conserva los
> agregados. La conclusión no depende de ella: se sostiene en el rango y en el orden.

### 5.4 La arbitrariedad que se corrigió, medida

Antes de atribuir al modelo la baja exactitud que se observaba, se midió cuánta información
contenía realmente la etiqueta. Se presentó al etiquetador exacto **la misma flota
permutada** —los mismos camiones, las mismas capacidades, una situación operativamente
idéntica— y se comparó su nueva respuesta con la original, ambas canonicalizadas
(`scripts/teacher_self_agreement.py`, 1.158 episodios de 2026 con dos o más camiones):

| | |
|---|---:|
| Exactitud que el etiquetador reproduce de sí mismo | **0,3820** |
| Concordancia por clase consigo mismo | **0,4449** |
| Episodios que reproduce de forma idéntica | 34,02 % |
| \|Δ vehículos cargados\| | **0,0000** |
| \|Δ CU aprovechada\| | **0,0000** |

El oráculo que genera las etiquetas reproduce menos del 40 % de ellas cuando se le permuta la
flota, mientras el resultado operativo es exactamente el mismo. Ésa fue la evidencia que
motivó ordenar la flota: si el orden de llegada de los camiones cambia el plan sin cambiar la
calidad del plan, y el modelo no observa ese orden, entonces esa parte de la etiqueta era
ruido inyectado por el generador.

Con la flota ordenada, esa fuente de variación ya no ocurre en los datos. Lo que queda —y no
conviene eliminar— es el desempate aleatorio del etiquetador entre vehículos **de la misma
clase**: dos filas de la misma clase son indistinguibles en las features, así que cuál de las
dos recibe el cupo es intrínsecamente impredecible. Fijarlo por identificador subiría la
exactitud pero introduciría un sesgo sistemático, excluyendo siempre a los mismos vehículos
en mezclas parecidas. Se rechazó deliberadamente.

### 5.5 El techo exacto, y cuánto de él se alcanza

Dos vehículos de la misma clase en el mismo episodio tienen features idénticas: misma `cu`,
mismo one-hot, mismo `n_misma_clase`, mismo contexto. Ninguna entrada los distingue, así que
la exactitud alcanzable está acotada en forma cerrada. Con `n(c,t)` = vehículos de la clase
`c` que el etiquetador mandó al destino `t`, y `m_c = Σ_t n(c,t)`
(`src/modeling/metrics.py:label_ceilings`):

```
Cota A  (modelo determinista por vehículo)  =  Σ_c max_t n(c,t)      / N
Cota B  (pipeline con decodificador)        =  Σ_c Σ_t n(c,t)² / m_c / N
```

| Partición de prueba (2026) | |
|---|---:|
| Cota A — techo de un clasificador determinista | **0,8997** |
| Cota B — techo del pipeline con decodificador | **0,8659** |
| Exactitud medida del modelo | **0,8458** |
| Fracción de la cota B alcanzada | **97,7 %** |

Sobre el conjunto completo las cotas son A = 0,8809 y B = 0,8417. La cifra es **invariante a
la canonicalización**: recalculada sin canonicalizar da exactamente los mismos 0,8809 y
0,8417, porque permutar el eje de destinos no altera `max_t` ni `Σ_t n²`.

> **El techo bajó, y eso es esperado.** Sobre el conjunto anterior la cota A era 0,9243 y la
> B 0,9005. Ordenar la flota equilibra el reparto de etiquetas, y un problema equilibrado es
> más difícil para un clasificador determinista que uno donde el 52 % de las filas comparte
> una sola etiqueta. Lo que importa es que el modelo pasó de alcanzar el **58,8 %** de su
> techo a alcanzar el **97,7 %**: la brecha que quedaba no era del modelo, era de la etiqueta.

---

## 6. Generalización fuera del sobre de entrenamiento

Cada episodio de entrenamiento cabe en un sobre estrecho: **1–4 camiones y hasta 20
vehículos** (`src/loading/scenarios.py`). Salir de ese sobre se mide en dos ejes, un
conjunto por eje, y en los dos el procedimiento es el mismo: cambiar **una sola variable**
y reetiquetar con el etiquetador exacto (`scripts/build_extrapolation_set.py`).

Los dos ejes dan respuestas distintas, y conviene no promediarlas: en el de camiones el
modelo deja de reproducir al maestro, y en el de manifiestos no.

### 6.1 Eje de camiones

Los datos de entrenamiento contienen entre uno y cuatro camiones. Como el perceptrón se
comparte entre todos los pares, **los mismos pesos** pueden puntuar manifiestos con más
camiones sin reconstruir ni reentrenar la red. Para comprobarlo se tomaron los mismos
manifiestos de prueba, se les cambió únicamente la flota y se reetiquetaron:

| Conjunto | Camiones | Violaciones | Brecha de conteo | Iguala el óptimo | Greedy |
|---|---|---:|---:|---:|---:|
| Prueba 2026 | 1–4 (visto en entrenamiento) | 0,0000 | +0,0242 | 97,58 % | +0,5990 |
| Extrapolación | 5–6 | 0,0000 | +0,0000 | 100,00 % | +0,0000 |
| Extrapolación | 8–10 | 0,0000 | +0,0000 | 100,00 % | +0,0000 |
| Extrapolación, capacidad total constante | 8–10 | 0,0000 | +0,0189 | 98,82 % | +0,0157 |

**Alcance de esta evidencia.** Queda demostrado que el modelo guardado **acepta y resuelve**
manifiestos con hasta diez camiones usando los mismos pesos, sin violar capacidad en ningún
episodio. No queda demostrada calidad a esa escala, por dos razones que conviene declarar:

1. **Los dos primeros conjuntos son triviales.** Al añadir camiones manteniendo el rango de
   capacidades del entrenamiento, la capacidad total crece (de 33,1 a 54,0 CU de media) y
   ningún vehículo queda diferido, de modo que el 100 % de coincidencia también lo alcanza la
   heurística greedy. No discriminan.
2. **En el único conjunto exigente, la ventaja sobre el greedy desaparece — y se invierte.**
   Con capacidad total constante (24,0 CU de media repartidos entre 8 a 10 camiones), el
   modelo deja una brecha de +0,0189 frente a +0,0157 del greedy, e iguala el óptimo en el
   98,82 % frente al 98,95 %. Es una diferencia pequeña, pero va en contra del modelo. En la
   versión anterior de este documento el signo era el opuesto (+0,0137 frente a +0,0157);
   sobre el conjunto regenerado ya no lo es.

A eso se añade que la concordancia por clase cae fuertemente fuera del rango entrenado:
0,9293 con 1–4 camiones, 0,1983 con 5–6 y 0,1144 con 8–10. El modelo sigue produciendo planes
factibles y de buen conteo, pero **deja de reproducir el reparto del etiquetador** en cuanto
la flota excede lo que vio. La extrapolación es, por tanto, una propiedad *arquitectónica*
demostrada —la red acepta flotas arbitrarias— y no una garantía de calidad.

### 6.2 Eje de tamaño de manifiesto

El otro tope del sobre es `MAX_N = 20`, el submuestreo por episodio. No es un detalle de
implementación: **el 51,0 % de los grupos cantón-semana reales lo supera** (mediana 21, p99
1.097, máximo 2.774), y el recorte descartó **1.916.093 vehículos**. Dicho de otro modo, la
mitad de los manifiestos que el sistema vería en operación son mayores que cualquiera que el
modelo haya visto.

El conjunto se construye levantando ese tope **sólo en el año de prueba** —el entrenamiento
no se toca— y reetiquetando con el maestro. Cada escalón es el mismo conjunto de 1.531
episodios de 2026 con más vehículos por manifiesto:

| Conjunto | Veh./ep. | Violaciones | Brecha de conteo | Iguala el óptimo | Concordancia | Greedy |
|---|---:|---:|---:|---:|---:|---:|
| Prueba 2026 (`MAX_N` = 20) | 15,3 | 0,0000 | +0,0242 | 97,58 % | 0,9293 | +0,5990 |
| Extrapolación, `max_n` = 25 | 18,6 | 0,0000 | +0,0438 | 96,21 % | 0,9218 | +0,9915 |
| Extrapolación, `max_n` = 30 | 21,0 | 0,0000 | +0,0621 | 94,71 % | 0,9142 | +1,4363 |
| Extrapolación, `max_n` = 40 | 25,3 | 0,0000 | +0,0885 | 93,12 % | 0,9164 | +2,2949 |
| Extrapolación, `max_n` = 50 | 29,0 | 0,0000 | +0,1021 | 92,98 % | 0,9224 | +2,9337 |

**Este eje sí discrimina, y el resultado es el contrario al anterior.** Tres lecturas:

1. **La factibilidad aguanta entera.** Cero violaciones de capacidad en los cinco conjuntos,
   incluidos manifiestos de 50 vehículos. No es mérito del clasificador sino del
   decodificador, que garantiza la partición por construcción (§ el módulo
   `capacity_decoder.py` y sus pruebas), y es justo lo que hace que la extrapolación sea
   segura de intentar.
2. **La degradación es suave, y la del greedy no.** La brecha del modelo se multiplica por
   4,2 (de +0,024 a +0,102) mientras la del greedy se multiplica por 4,9 partiendo de un
   valor 25 veces mayor: a 50 vehículos el greedy deja **29 veces** más vehículos sin cargar
   que el modelo. La ventaja sobre la heurística no se erosiona al crecer el manifiesto —
   **se ensancha**.
3. **La concordancia por clase no se desploma.** Se mantiene entre 0,914 y 0,922 en los
   cuatro escalones, frente al 0,9293 dentro del sobre. Es el contraste que importa con
   §6.1: al añadir camiones el modelo dejaba de reproducir el reparto del maestro (0,11),
   mientras que al añadir vehículos lo sigue reproduciendo. Tiene sentido —el eje de
   camiones cambia el espacio de etiquetas, y el de vehículos no— pero era una hipótesis
   hasta medirla.

Estos conjuntos son además los **exigentes** que el §8 pedía: la proporción de vehículos
diferidos sube del 4,13 % al 15,18 % al pasar de 20 a 50, porque el manifiesto crece contra
una flota que no cambia. El déficit de capacidad aparece solo, sin forzarlo.

#### Hasta dónde llega el maestro

El conjunto sólo sirve mientras exista un óptimo **certificado** contra el que medir: el
etiquetador devuelve `optimal=False` si agota su presupuesto de 5 s, y
`dataset.drop_non_optimal` descarta esos episodios. Cuántos se pierden es, en sí mismo, un
resultado:

| `max_n` | Certifica | Sin certificar | Búsqueda media | p99 |
|---:|---:|---:|---:|---:|
| 20 | 100,00 % | 0 | 6,4 ms | 114,9 ms |
| 25 | 100,00 % | 0 | 31,4 ms | 577,7 ms |
| 30 | 100,00 % | 0 | 58,4 ms | 1.168,8 ms |
| 40 | 99,67 % | 5 | 132,7 ms | 3.391,2 ms |
| 50 | 98,56 % | 22 | 199,7 ms | 5.002,6 ms |

El maestro llega **bastante más lejos de lo que el tope de 20 sugería**: certifica todos los
episodios hasta 30 vehículos y todavía el 99,67 % a 40. El motivo es estructural —la
búsqueda es un programa dinámico memoizado sobre `(camión, conteos restantes por clase)`, así
que el coste crece polinómicamente con el número de vehículos y exponencialmente con el de
**clases**, que aquí son cuatro y fijas. Los episodios que se rinden son homogéneos: los 5 de
`max_n` = 40 son todos manifiestos de exactamente 40 vehículos con 3 o 4 camiones.

Queda un eje sin medir, el de **número de clases**, que por lo anterior es el que más
encarece la búsqueda exacta. No se construyó porque las seis clases fuera de alcance de
`config/vehicle_classes.yaml` no tienen CU asignado, y asignárselo cambiaría el alcance del
problema en lugar de sólo el conjunto de prueba.

---

## 7. Conclusiones

1. **La restricción de capacidad se cumple siempre.** Cero violaciones en 34.839 episodios,
   por construcción del decodificador y no por acierto del clasificador.
2. **Sobre el objetivo primario el modelo es claramente superior a la heurística:** brecha
   de optimalidad del 0,15 % frente al 4,17 % del greedy, y 97,58 % de episodios que igualan
   el conteo óptimo frente al 87,98 %.
3. **El modelo aporta tanto en qué se carga como en qué camión.** La ablación con logits
   nulos lo cuantifica en las dos dimensiones: sin el modelo, la brecha de conteo se
   multiplica por diez y la concordancia por clase cae de 0,9293 a 0,3092. Reproduce el plan
   completo del etiquetador en el 76,75 % de los episodios.
4. **La generalización fuera del sobre depende del eje, y hay que decirlo separado (§6).**
   En el de **camiones**, la arquitectura por pares cumple el requisito de flota sin límite
   codificado —se verificó sobre manifiestos de diez camiones sin reentrenar—, pero es una
   propiedad arquitectónica, **no una garantía de calidad**: la concordancia por clase se
   desploma a 0,11 y en el único conjunto exigente el greedy queda ligeramente por delante.
   En el de **tamaño de manifiesto** el resultado es el opuesto y es el que responde a la
   pregunta operativa: con manifiestos de hasta 50 vehículos —el 51 % de los reales supera
   los 20 que vio el modelo— la concordancia se mantiene en 0,92, la brecha se degrada
   suavemente (+0,024 → +0,102) y la ventaja sobre el greedy **se ensancha** hasta 29×. Cero
   violaciones de capacidad en los dos ejes.
5. **La baja exactitud que se observaba era una propiedad del generador de datos, y se
   corrigió.** El orden aleatorio de la flota cambiaba el plan del etiquetador sin ser una
   entrada observable. Ordenándola, el mismo modelo con los mismos hiper-parámetros pasa de
   0,5297 a **0,8458**, y de alcanzar el 58,8 % de su techo a alcanzar el **97,7 %**. Lo que
   queda es ruido irreducible por diseño: el desempate entre vehículos indistinguibles.
6. **El techo no está en los hiper-parámetros.** Ver §5.3.
7. **La latencia (43 ms por manifiesto, p99 56 ms) es holgada** frente al requisito
   operativo, aunque está dominada por la sobrecarga de una llamada de inferencia por
   manifiesto —varía entre 33 y 43 ms según la corrida— y no por el cómputo del modelo, que
   tiene 4.482 parámetros.

## 8. Trabajo pendiente identificado

- **Cerrar la brecha de CU.** El greedy aprovecha más capacidad. Una función de pérdida que
  penalice el desperdicio, o un decodificador que reordene por CU cuando la capacidad
  escasea, son las dos vías inmediatas. Es el único eje donde el modelo pierde.
- **Mejorar `SIN CAMIÓN`,** la etiqueta con peor cobertura (64,7 %). Decidir que un vehículo
  no viaja depende del estado acumulado del manifiesto, que el modelo por pares sólo ve a
  través del contexto agregado.
- **Reentrenar los otros cuatro modelos** sobre el conjunto regenerado y consolidarlos en la
  tabla de la sección VII. Requiere antes unificar partición, métricas y convención de
  etiqueta — ver [`08_comparabilidad_cinco_modelos.md`](../decisiones/03_comparabilidad.md).
- **Cerrar el tercer eje de extrapolación: el número de clases.** Los de camiones y tamaño de
  manifiesto ya están medidos (§6); el de clases es el que más encarece la búsqueda exacta y
  el único que sigue sin evidencia. Requiere antes decidir qué CU se asigna a las seis clases
  hoy fuera de alcance, que es una decisión de alcance del problema, no de evaluación.
- **Ablación de `canton`**, hoy excluido por no participar en la restricción de capacidad.
