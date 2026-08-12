# Scenarios Coverage

> **Auto-generated.** Reproduce with:
> ```bash
> python3 scripts/build_scenarios.py
> ```

**Generated:** 2026-08-08 20:05 UTC
**Elapsed:** 852.8s
**Floor (min N kept):** 5
**Max N per episode (subsample cap):** 20

---

## Episode universe

| | |
|---|---|
| Grupos semana-cantón totales | 55,076 |
| Excluidos por piso (N<5) | 20,237 |
| Episodios construidos y etiquetados | 34,839 |

## Resultado del labeler

| | |
|---|---|
| Filas en episode_vehicles.parquet | 534,680 |
| Episodios triviales (nadie deferido) | 29,860 (85.7%)
| Episodios no-óptimos (time_budget agotado) | 0 |
| search_time_ms promedio | 20.1
| search_time_ms p99 | 329.1
