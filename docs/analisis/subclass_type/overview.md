# Subclase y tipo

Desglose de las matriculaciones por **subclase** (`PLATAFORMA-C`, `CAMIONETA`,
…) y por **tipo** (`PESADO`, `LIVIANO`, …).

- Ambos gráficos agregan todo el período **2017-2026** (ver la nota de
  [matriculaciones totales](../registrations/totals.md) sobre por qué aquí sí
  entra 2017).
- Los mapas de calor usan el estilo compartido de `visual_helpers`: fondo
  oscuro, mapa de color *viridis*, 150 dpi.
- Las figuras se generan en `reports/figures/proposals/subclass_type/` mediante
  `scripts/reporting/proposals/solution_visuals/subclass_type/`.

La etapa reutiliza la configuración y las utilidades de la visualización
`class_location`, que resuelve el mismo problema con otro par de ejes.
