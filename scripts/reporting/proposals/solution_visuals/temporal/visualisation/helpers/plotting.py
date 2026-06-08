# -*- coding: utf-8 -*-
"""Plotting logic helpers for vehicle trends visualization.

Keeps orchestrator scripts thin by isolating the detailed plotting loop concerns.
"""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from .aggregation import _aggregate_series, _aggregate_series_multi

from .style import _draw_aligned_labels, _render_annotation_table


def _plot_trend_lines(
    ax: plt.Axes,
    plot_dates: pd.DatetimeIndex,
    sub_df: pd.DataFrame,
    unique_dates: list,
    class_colors: dict[str, str],
) -> None:
    """Plot Class (solid), Sub-class (dashed), and Type (dotted) trends with parent-shaded colors and direct labels."""
    labels_to_plot = []

    # Get top 3 sub-classes and top 3 types by volume for this canton to reduce noise
    top_sub_classes = set()
    if "sub_class" in sub_df.columns:
        top_sub_classes = set(sub_df.groupby("sub_class")["count"].sum().nlargest(3).index)

    top_types = set()
    if "type" in sub_df.columns:
        top_types = set(sub_df.groupby("type")["count"].sum().nlargest(3).index)

    # 1. Class lines – solid
    for cls in sub_df["class"].unique():
        cls_df = sub_df[sub_df["class"] == cls]
        series = _aggregate_series(cls_df, unique_dates)
        color = class_colors.get(cls, "#6a994e")
        ax.plot(plot_dates, series / 1000, label=cls, color=color, linewidth=2.0, linestyle="-")
        
        last_val = series.iloc[-1] / 1000
        if last_val > 0.05:
            labels_to_plot.append((last_val, cls, color, 0.9))

    # 2. Sub‑class trends – dashed, shaded color
    if "sub_class" in sub_df.columns:
        sub_series_map = _aggregate_series_multi(sub_df, unique_dates, group_by=["class", "sub_class"])
        for (cls, sub_class), series in sub_series_map.items():
            if sub_class not in top_sub_classes:
                continue
            color = class_colors.get(cls, "#6a994e")
            ax.plot(plot_dates, series / 1000, label="_nolegend_", color=color, linewidth=1.0, linestyle="--", alpha=0.6)
            
            last_val = series.iloc[-1] / 1000
            if last_val > 0.05:
                labels_to_plot.append((last_val, sub_class, color, 0.7))

    # 3. Type trends – dotted, shaded color
    if "type" in sub_df.columns:
        type_series_map = _aggregate_series_multi(sub_df, unique_dates, group_by=["class", "type"])
        for (cls, typ), series in type_series_map.items():
            if typ not in top_types:
                continue
            color = class_colors.get(cls, "#6a994e")
            ax.plot(plot_dates, series / 1000, label="_nolegend_", color=color, linewidth=1.0, linestyle=":", alpha=0.4)
            
            last_val = series.iloc[-1] / 1000
            if last_val > 0.05:
                labels_to_plot.append((last_val, typ, color, 0.5))

    # Render a compact annotation table beside the plot
    _render_annotation_table(ax, labels_to_plot)
