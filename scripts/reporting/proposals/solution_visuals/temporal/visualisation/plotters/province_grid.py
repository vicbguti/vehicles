# -*- coding: utf-8 -*-
"""Compatibility shim for province‑level grid plotter.

The original implementation lives in ``visualisation.plot_province_grid``. This
module simply re‑exports the function so that ``visualisation.plotters`` can be
imported without errors.
"""

from ..plot_province_grid import plot_province_grid  # noqa: F401
