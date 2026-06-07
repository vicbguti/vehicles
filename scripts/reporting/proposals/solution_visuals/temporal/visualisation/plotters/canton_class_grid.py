# -*- coding: utf-8 -*-
"""Plot canton‑class temporal trends with premium styling.

This orchestrator wires together validation, layout, aggregation, styling, and
legend helpers to keep the implementation thin and maintainable.
"""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

# Shared style utilities
from ..style import apply_layout, get_palette

# Helper modules
from ..helpers.validation import validate_canton_grid_input
from ..helpers.layout import create_grid
from ..helpers.plotting import _plot_trend_lines
from ..helpers.style import _apply_style
from ..helpers.legend import build_proxy_legend

# Geo‑mapper for canton names
from utils.geo_mapper.mapper import code_to_name
from pandas.tseries.offsets import MonthEnd


def plot_canton_class_grid(df: pd.DataFrame, cantons: list | None, out_path: str) -> None:
    """Create a facet grid of temporal trends for each canton.

    Parameters
    ----------
    df : pd.DataFrame
        Expected columns: ``date_label``, ``canton``, ``class``, ``sub_class``,
        ``type``, ``count``.
    cantons : list | None
        Optional list of canton identifiers to plot. ``None`` means all cantons.
    out_path : str
        Destination file path for the PNG image.
    """
    # ---------------------------------------------------------------------
    # 1. Validate input and optionally filter cantons
    # ---------------------------------------------------------------------
    df = validate_canton_grid_input(df, cantons)

    # ---------------------------------------------------------------------
    # 2. Determine layout
    # ---------------------------------------------------------------------
    unique_cantons = sorted(df["canton"].unique())
    fig, axes = create_grid(len(unique_cantons))

    # ---------------------------------------------------------------------
    # 3. Colour palette for vehicle classes
    # ---------------------------------------------------------------------
    palette = get_palette()
    class_colors = {cls: palette[i % len(palette)] for i, cls in enumerate(df["class"].unique())}

    # ---------------------------------------------------------------------
    # 4. Pre‑compute the full ordered date list for re‑indexing
    # ---------------------------------------------------------------------
    unique_dates = df["date_label"].unique()
    plot_dates = pd.to_datetime(unique_dates)

    # ---------------------------------------------------------------------
    # 5. Plot each canton
    # ---------------------------------------------------------------------
    for ax, canton in zip(axes, unique_cantons):
        sub_df = df[df["canton"] == canton]

        # Delegate plot creation to plotting helper
        _plot_trend_lines(ax, plot_dates, sub_df, unique_dates, class_colors)

        # Axis styling
        canton_name = code_to_name(str(canton)) or str(canton)
        _apply_style(ax, f"Canton: {canton_name}")

    # Extend X limit to make room for direct labels on the right
    if len(plot_dates) > 0:
        new_max = plot_dates[-1] + MonthEnd(12)
        axes[0].set_xlim(right=new_max)

    # ---------------------------------------------------------------------
    # 6. Hide any unused axes (when number of cantons is not a perfect grid)
    # ---------------------------------------------------------------------
    for i in range(len(unique_cantons), len(axes)):
        axes[i].axis("off")

    # ---------------------------------------------------------------------
    # 7. Build the global legend with proxies for sub‑class and type
    # ---------------------------------------------------------------------
    build_proxy_legend(fig, axes)

    # ---------------------------------------------------------------------
    # 8. Apply overall layout and save figure
    # ---------------------------------------------------------------------
    apply_layout(fig, title="Monthly Vehicle Registrations by Canton, Class (2017‑2026)")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Canton‑class visual saved to {out_path}")
