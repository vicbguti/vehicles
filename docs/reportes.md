# Generación de reportes

`scripts/reporting/` construye los Markdown y las figuras de `reports/`. Es la
única parte del repositorio donde `reports/` se escribe: todo lo que hay ahí es
**salida de build**, no documentación escrita a mano.

## Orquestadores

```bash
uv run python scripts/run_pipeline.py     # perfilado + reportes, todo seguido
uv run python scripts/run_reporting.py    # solo los reportes
```

| Sub-orquestador | Qué construye |
|---|---|
| `run_audits.py` | Las auditorías de calidad y volumen |
| `run_proposals.py` | Las figuras de la propuesta |

`stage_groups/` (`temporal.py`, `spatial.py`, `class_location.py`) es la **única
fuente de verdad de qué etapas se ejecutan**. Si un módulo de `proposals/` no
aparece ahí, es código muerto.

## Auditorías (`scripts/reporting/audits/`)

| Script | Salida |
|---|---|
| `summary.py` | `reports/00_executive_summary.md` |
| `quality.py` | `reports/01_quality_audit.md` |
| `volume/storage.py` | `reports/02_volume/storage.md` |
| `volume/growth_trends.py` | `reports/02_volume/growth_trends.md` |
| `volume/memory_profile.py` | `reports/02_volume/memory_profile.md` |
| `visuals.py` | `reports/figures/audits/` |

Ver [auditorías de datos](auditorias.md).

## Figuras de la propuesta (`scripts/reporting/proposals/solution_visuals/`)

Cuatro familias: `spatial/` (distribución de clases, demandas geográficas),
`temporal/` (tendencias por clase, por ubicación y combinadas),
`class_location/` y `subclass_type/`. Todas escriben en
`reports/figures/proposals/`, que el sitio publica a través de
`docs/propuesta/figuras`.

!!! warning "Una etapa no corre en un clon limpio"
    `spatial/geographic_demands.py` necesita `data/raw/SRI_Vehiculos_DD.xlsx`
    —el diccionario Excel del SRI— que está en `.gitignore` y **no viene en el
    clon**. Es la única etapa que lo usa, y falla sin él. Mientras no se
    consiga ese archivo, las figuras versionadas de esa etapa no se pueden
    regenerar ni verificar.

## Deuda conocida

Este árbol concentra 329 de los errores de linting pendientes y tiene código
duplicado sin cablear en `stage_groups`. Sanearlo requiere poder regenerar las
figuras para demostrar por comparación de píxeles que nada cambia — es decir,
requiere el `.xlsx` de arriba.
