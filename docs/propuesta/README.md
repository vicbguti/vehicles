# La propuesta

Documentos de la propuesta del proyecto. En orden de lectura:

1. [El problema](01_problem.md) — contexto real y restricciones de capacidad
2. [Los datos](03_data.md) — del dataset del SRI a los episodios de entrenamiento
3. [Evaluación](05_evaluation.md) — métricas y caso de estudio
4. [Viabilidad](06_feasibility.md) — estudio del tamaño de episodio (reproducible con `scripts/loading/episode_feasibility.py`)
5. [Cobertura de features](08_feature_coverage.md)
6. [Cobertura de escenarios](09_scenarios_coverage.md)

**Caso de estudio:** [example/](example/README.md) — comparación con 18
vehículos (procedimiento actual vs. greedy vs. carga óptima).

**Figuras:** [solution/visuals/](solution/visuals/README.md) — distribución de
clases, geografía y estacionalidad.

**Archivo:** [deferred/](deferred/README.md) — ruteo, aprendizaje por refuerzo
profundo y propuestas superadas. **Fuera del alcance actual.**

!!! info "Dos documentos se movieron"
    El alcance y el método originales describían un diseño que ya no es el
    vigente (PyTorch, dos camiones fijos, archivos que nunca existieron). Están
    en [histórico](../historico/02_alcance_original.md) con el aviso
    correspondiente. Lo que se construyó de verdad está en
    [estructura del código](../estructura.md) y
    [pipeline Kedro](../pipeline_kedro.md).
