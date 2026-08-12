# Perfilado del dataset

`scripts/profiling/` recorre los CSV del SRI y deja cachés intermedias en
`reports/cache/`, que después consumen los generadores de reportes. Ninguna de
estas etapas toca el modelado.

| Script | Qué calcula |
|---|---|
| `disk.py` | Tamaño en disco de cada CSV y huella física total |
| `annual.py` | Esquema anual: tipos, cardinalidad y completitud por columna |
| `evolution.py` | Deriva temporal del esquema y evolución del volumen de registros |

La lógica vive en `src/profiler/`, organizada por dimensión: `integrity/`
(completitud, unicidad, atípicos, estadísticos), `structure/` (tipos,
cardinalidad, conformidad, evolución), `temporal/` (conteo de registros,
estacionalidad, crecimiento interanual) y `physical/` (disco, memoria).

## Ejecutar

```bash
uv run python scripts/run_profiling.py
```

Requiere que los CSV estén descargados de verdad: sin `git lfs pull` son
punteros de 133 bytes y el perfilado produce cifras sin sentido **sin fallar**.
Ver [Git LFS](git_lfs.md).
