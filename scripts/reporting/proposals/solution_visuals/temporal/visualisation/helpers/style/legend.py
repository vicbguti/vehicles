# -*- coding: utf-8 -*-
"""Legend / annotation‑table helper for visualisation plotters.

Provides a compact table placed beside the plot that lists the label text
and its numeric value (in thousands). The table inherits the original
label colours for visual consistency.
"""

from __future__ import annotations
import matplotlib.pyplot as plt

def _render_annotation_table(ax: plt.Axes, items: list[tuple[float, str, str, float]]) -> None:
    """Render a compact legend table beside the plot.

    Parameters
    ----------
    ax: plt.Axes
        The axis of the main plot.
    items: list of (value, label, color, alpha)
        Prepared label items (same structure as ``labels_to_plot``).
    """
    if not items:
        return
    # Build rows: label text and numeric value (k)
    rows = []
    for value, text, color, alpha in items:
        rows.append([text, f"{value:.2f}k"])

    # Create the table on the right side of the axis
    table = ax.table(
        cellText=rows,
        colLabels=["Label", "Value (k)"],
        cellLoc="left",
        loc="right",
        bbox=[1.05, 0.0, 0.35, 1.0],
    )
    # Style header and rows
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_fontsize(8)
            cell.set_text_props(weight="bold")
        else:
            # Apply original colour to label column
            if col == 0:
                label_color = items[row - 1][2]
                cell.set_text_props(color=label_color)
            cell.set_fontsize(8)
    table.auto_set_font_size(False)
    table.scale(1, 1.2)
