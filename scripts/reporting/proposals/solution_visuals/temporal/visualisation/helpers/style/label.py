# -*- coding: utf-8 -*-
"""Label‑rendering helper for visualisation plotters.

These utilities draw direct text labels on the axis together with optional
leader lines. They operate on the output of ``adjust_label_positions``.
"""

from __future__ import annotations
import matplotlib.pyplot as plt

def _draw_aligned_labels(
    ax: plt.Axes,
    adjusted_labels: list[tuple[float, float, str, any, float]],
    last_date: any,
    text_date: any,
    line_end_date: any,
) -> None:
    """Render direct text labels on the axis with matching pointer lines.

    Parameters
    ----------
    ax: plt.Axes
        The axis to annotate.
    adjusted_labels: list of (orig_y, adj_y, text, color, alpha)
        Labels that have already been vertically spaced.
    last_date, text_date, line_end_date: datetime‑like
        Dates used to position the label text and the leader line.
    """
    for orig_y, adj_y, text, color, alpha in adjusted_labels:
        ax.text(
            text_date,
            adj_y,
            text,
            color=color,
            fontsize=7,
            va="center",
            ha="left",
            alpha=alpha,
            clip_on=True,
        )
        # Draw a thin gray pointer line if adjusted significantly
        if abs(adj_y - orig_y) > 0.05:
            ax.plot(
                [last_date, line_end_date],
                [orig_y, adj_y],
                color="gray",
                linestyle=":",
                linewidth=0.5,
                alpha=0.5,
            )
        else:
            # Short connector line for visual alignment
            ax.plot(
                [last_date, line_end_date],
                [orig_y, orig_y],
                color=color,
                linestyle="-",
                linewidth=0.3,
                alpha=0.3,
            )
