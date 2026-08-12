# Auditorías de datos

Salida generada por `scripts/reporting/audits/`. Estos archivos **no se editan a
mano**: se regeneran con `uv run python scripts/run_reporting.py`. Si hay que
cambiar lo que dicen, se cambia el generador.

| Archivo | Contenido |
|---|---|
| `reports/00_executive_summary.md` | Perfil general: cobertura temporal, volumen total y estado de viabilidad |
| `reports/01_quality_audit.md` | Completitud por columna, porcentaje de nulos, atípicos y duplicados |
| `reports/02_volume/storage.md` | Tamaño en disco de cada CSV |
| `reports/02_volume/growth_trends.md` | Variación interanual del número de matriculaciones |
| `reports/02_volume/memory_profile.md` | Uso de RAM y estimación del ahorro al convertir columnas a `category` de pandas |

La figura de tendencias interanuales queda en `reports/figures/audits/`.

Ver también [deduplicación](deduplicacion.md), que documenta la limpieza que
dejó los CSV en el estado que estas auditorías miden.
