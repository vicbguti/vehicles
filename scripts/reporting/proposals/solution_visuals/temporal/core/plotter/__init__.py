"""Compatibility shim for legacy imports.

Old code may import ``temporal.core.plotter.canton_class_grid`` or
``temporal.core.plotter.province_grid``. This module re‑exports the new
implementations from ``visualisation`` so existing imports continue to work.
"""

from visualisation import plot_canton_class_grid  # noqa: F401
from visualisation.plot_province_grid import plot_province_grid  # noqa: F401
