# -*- coding: utf-8 -*-
"""Layout helper for visualisation plotters.

Provides a thin wrapper that computes an appropriate grid size for a given
number of sub‑plots and returns a ``matplotlib`` Figure and a flat list of Axes.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

def create_grid(num_plots: int, max_cols: int = 4):
    """Create a Matplotlib figure with a suitable grid layout.

    Parameters
    ----------
    num_plots: int
        Number of sub‑plots required.
    max_cols: int, optional
        Maximum number of columns in the grid (default 4).

    Returns
    -------
    fig: matplotlib.figure.Figure
    axes: list[matplotlib.axes.Axes]
        Figure and a flat list of Axes objects.
    """
    ncols = min(max_cols, num_plots)
    nrows = (num_plots + ncols - 1) // ncols
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(4 * ncols, 3 * nrows),
        sharex=True,
        sharey=True,
    )
    # Ensure a flat list regardless of shape
    axes = axes.flatten() if isinstance(axes, (list, np.ndarray)) else [axes]
    return fig, axes


def adjust_label_positions(
    labels: list[tuple[float, str, any, float]], min_diff: float = 0.4
) -> list[tuple[float, float, str, any, float]]:
    """Sort labels by original Y coordinate and space them vertically to prevent overlapping.

    Parameters
    ----------
    labels : list of (orig_y, text, color, alpha)
    min_diff : float
        Minimum vertical distance between labels.

    Returns
    -------
    list of (orig_y, adj_y, text, color, alpha)
    """
    if not labels:
        return []
    sorted_labels = sorted(labels, key=lambda x: x[0])
    adjusted = []
    for orig_y, text, color, alpha in sorted_labels:
        adj_y = orig_y
        if adjusted:
            prev_adj_y = adjusted[-1][1]
            if adj_y - prev_adj_y < min_diff:
                adj_y = prev_adj_y + min_diff
        adjusted.append((orig_y, adj_y, text, color, alpha))
    return adjusted

