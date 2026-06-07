"""Core helpers for temporal visualisation scripts (loader, aggregator, plotter).

Provides a stable public API: aggregate_by_province, aggregate_by_province_class, aggregate_by_class, aggregate_overall, plot_location_grid, plot_combined_grid, trim_zero_tail, DEFAULT_EXCLUDE.
"""

from .aggregator.by_province import aggregate_by_province
from .aggregator.by_class import aggregate_by_class
from .aggregator.overall import aggregate_overall
from .aggregator.combined import aggregate_combined
from .plotter.location import plot_location_grid
from .plotter.combined import plot_combined_grid
from ..utils.time_series.trimming import trim_zero_tail, DEFAULT_EXCLUDE

__all__ = [
    "aggregate_by_province",
    "aggregate_by_class",
    "aggregate_overall",
    "aggregate_combined",
    "plot_location_grid",
    "plot_combined_grid",
    "trim_zero_tail",
    "DEFAULT_EXCLUDE",
]
