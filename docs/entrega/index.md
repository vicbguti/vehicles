# Tarea #4 — Entregables de Juan Francisco Fernández Ramos

Índice de lo producido para la Tarea #4, con su destino en el reporte del grupo
(el Google Doc en formato IEEE).

| Archivo | Qué es | Dónde va |
|---|---|---|
| [`01_tabla_v_caso_uso_analisis.md`](../entrega/tabla_v_caso_uso.md) | Los dos escenarios del caso de uso de análisis | **Tabla V**, pág. 13 — reemplaza los marcadores `1.`, `2a.`, `a` |
| [`02_seccion_VI_D_mlp.md`](../modelo/arquitectura_mlp.md) | Arquitectura, plataforma, esquema de datos e hiper-parámetros justificados, con dos diagramas UML | **Sección VI-D**, pág. 25 — hoy vacía |
| [`03_resultados_mlp.md`](../modelo/resultados.md) | Resultados medidos, ablaciones y limitaciones | **Sección VII** — aporta la parte del MLP |
| [`04_anexo_ia_juan.md`](../entrega/anexo_uso_de_ia.md) | Preguntas, respuestas, qué se aceptó y qué se rechazó | **Anexo A, B y C** |
| [`05_hallazgos_para_el_equipo.md`](../decisiones/01_hallazgos_transversales.md) | Lo que afecta a los cinco modelos y los vacíos sin dueño | **Interno — no va al reporte** |
| [`06_canonicalizacion_y_etiquetado.md`](../modelo/canonicalizacion.md) | Las cuatro fuentes de arbitrariedad de la etiqueta, el techo exacto de exactitud y el arreglo medido | **Interno**, salvo §5 y §8 → **VII** y **VIII** |
| [`07_mensaje_al_equipo.md`](../decisiones/02_orden_de_flota.md) | Versión corta del `06_` para enviar por chat, con la decisión que hay que tomar | **Interno — para Víctor y Nicolás** |
| [`08_comparabilidad_cinco_modelos.md`](../decisiones/03_comparabilidad.md) | Por qué la tabla de la §VII no se puede construir hoy: partición, métricas y etiqueta divergen entre `src/modeling/` y `fleet_loading/` | **Interno — para Víctor y Nicolás** |

Transcripción de la sesión de IA:
[`chat/2026-07-25-05-juan-mlp-design-training-evaluation.md`](https://github.com/vicbguti/vehicles/blob/main/chat/2026-07-25-05-juan-mlp-design-training-evaluation.md).

---

## Resumen de lo entregado

**Los cuatro entregables asignados en la planificación (págs. 4, 6, 7 y 8) están
completos**, con resultados medidos sobre el conjunto de datos completo — 34.839
episodios y 534.680 filas — y no sobre la muestra de 200 episodios.

Titulares:

- El plan entregado **nunca excede la capacidad** de un camión, en ninguno de los 34.839
  episodios.
- Sobre el objetivo primario —cuántos vehículos se transportan— el modelo **iguala la
  solución óptima en el 97,58 %** de los episodios de prueba, frente al 87,98 % de la
  heurística greedy, y reproduce el plan completo del etiquetador en el **76,75 %**.
- La arquitectura de puntuación por par cumple el requisito de flota sin límite codificado:
  se verificó ejecutando **los mismos pesos sobre manifiestos de diez camiones**, sin
  reentrenar.
- **La causa de la baja exactitud se encontró, se midió y se corrigió.** El generador
  devolvía las capacidades de la flota en orden aleatorio, lo que fijaba cuál de los planes
  óptimos empatados producía el etiquetador — información ausente de las entradas del modelo
  y por tanto imposible de aprender. Ordenar la flota antes de etiquetar (una línea en
  `src/loading/scenarios.py`) lleva al mismo modelo, con los mismos hiper-parámetros y la
  misma semilla, de **0,5297 a 0,8458** de exactitud y de **0,2996 a 0,8131** de F1 macro,
  **sin mover las métricas operativas**. El modelo pasa de alcanzar el 58,8 % de su techo
  exacto a alcanzar el **97,7 %**.

Limitaciones declaradas, no ocultadas: el modelo **pierde frente al greedy en aprovechamiento
de CU** (+0,0760 contra +0,0007), `SIN CAMIÓN` es la etiqueta peor resuelta (64,7 % de
cobertura), y la generalización a flotas grandes está demostrada como factibilidad, no como
calidad — en el único conjunto de extrapolación exigente el greedy queda ligeramente por
delante.

> **Correcciones registradas.**
> **27 de julio.** Una versión anterior de este resumen concluía que "cerca del 60 % de la
> etiqueta es ruido irreducible", apoyándose en la auto-concordancia del etiquetador
> (0,3983). Esa cifra nunca fue un techo. Calculado el techo real, la mayor parte de esa
> brecha resultó **eliminable**, no irreducible.
> **6 de agosto.** El equipo acordó aplicar la corrección y el conjunto se regeneró. Con ello
> cae una conclusión anterior: se afirmaba que el modelo **no aportaba a la elección de
> camión**, apoyándose en una ablación donde la concordancia por clase era 0,5507 con modelo
> y 0,5469 sin él. Sobre el conjunto corregido esa misma ablación da **0,9293 contra
> 0,3092**: el modelo sí aporta, y mucho. No era que no supiera elegir camión — era que sobre
> aquellas etiquetas no había nada aprendible que elegir. Detalle en
> [`06_canonicalizacion_y_etiquetado.md`](../modelo/canonicalizacion.md) y cifras
> vigentes en [`03_resultados_mlp.md`](../modelo/resultados.md).

---

## Reproducir

```bash
git lfs install && git lfs pull                     # 522 MB de datos reales -- ver docs/git_lfs.md
uv sync                                             # .python-version ya fija 3.12
uv run python scripts/build_vehicle_features.py     # ~1 min
uv run python scripts/build_scenarios.py            # ~7 min
uv run python scripts/train_mlp.py                  # ~2 min en CPU
uv run python scripts/evaluate_mlp.py               # incluye la ablación de logits nulos
uv run python scripts/teacher_self_agreement.py --years 2026
uv run python scripts/label_ceiling.py              # techo exacto de exactitud
uv run python scripts/sweep_mlp.py                  # 8 configuraciones, ~25 min
uv run pytest                                       # 430 pruebas
```

> El experimento del orden de la flota
> (`artifacts/mlp/fleet_order_experiment/build_sorted_episodes.py`) ya **no hace falta para
> reproducir estos resultados**: era el modo de medir el efecto sin tocar `data/episodes/`,
> y el arreglo que proponía está aplicado en `generate_fleet()`. Se conserva como evidencia
> del §6 del documento 06 y para poder reconstruir el conjunto *anterior* si hiciera falta
> comparar, con `--order as-is`.

> **Nota de entorno.** El intérprete del sistema es Python 3.14 y TensorFlow 2.21 sólo
> publica ruedas hasta CPython 3.13. Sin el `--python 3.12` el entorno no puede instalar
> Keras.

Extrapolación a flotas mayores:

```bash
uv run python scripts/build_extrapolation_set.py --n-trucks 8 10 --cap-mode constant-total
uv run python scripts/evaluate_mlp.py --split single --policy model \
    --episodes-dir data/episodes/extrap_8_10_constanttotal \
    --out-name metrics_extrap_8_10_constanttotal.json
```

## Código añadido

Casi todo es **aditivo**: no se modificó `src/loading/labeler.py` ni
`scripts/build_scenarios.py`. La única excepción es deliberada y acordada con el equipo:
`generate_fleet()` en `src/loading/scenarios.py` ahora ordena las capacidades antes de
etiquetar. Ese cambio obliga a **regenerar el conjunto y reentrenar los cinco modelos**.

```
config/mlp.yaml
pyproject.toml + uv.lock
src/modeling/{canonicalization,dataset,features,mlp_classifier,capacity_decoder,metrics}.py
scripts/{train_mlp,evaluate_mlp,sweep_mlp,build_extrapolation_set,teacher_self_agreement}.py
scripts/label_ceiling.py
tests/                     430 pruebas (325 del maestro exacto)
artifacts/mlp/             modelo, métricas, curvas, matriz de confusión
artifacts/mlp/fleet_order_experiment/   evidencia del §6 del documento 06
```
