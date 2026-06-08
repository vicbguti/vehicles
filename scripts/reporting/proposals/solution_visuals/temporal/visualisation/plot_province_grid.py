# -*- coding: utf-8 -*-
"""Province‑level wrapper for canton‑class grids with premium styling.

This module mirrors the original ``core.plotter.province_grid`` but uses the
shared style utilities from ``visualisation.style``.
"""

import pandas as pd
from typing import List

# Style helpers
from .style import apply_layout, get_palette, format_date_axis
from .plotters.canton_class_grid import plot_canton_class_grid


def plot_province_grid(
    df: pd.DataFrame,
    canton_codes: List[str],
    out_path: str,
    province_name: str | None = None,
) -> None:
    """Create a canton‑class grid for all cantons of a given province.

    Parameters
    ----------
    df : pd.DataFrame
        Full DataFrame produced by the canton aggregation step.
    canton_codes : list[str]
        List of canton identifiers belonging to the province.
    out_path : str
        Destination PNG file.
    province_name : str, optional
        Human‑readable province name used for the figure title.
    """
    if not canton_codes:
        print(f"No cantons found for province {province_name!r}, skipping plot.")
        return
    sub_df = df[df["canton"].isin(canton_codes)]
    # Re‑use the existing grid function; it will handle title per canton.
    plot_canton_class_grid(sub_df, cantons=canton_codes, out_path=out_path)
    # Optionally add a global title (the layout helper can add a figure title).
    # This could be enhanced by passing a title to ``plot_canton_class_grid``.
    print(f"Province‑level canton‑class visual saved to {out_path}")
