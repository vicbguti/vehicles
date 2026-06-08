# -*- coding: utf-8 -*-
"""Legend helper for visualisation plotters.

Provides a function to build a global legend that includes the class handles
plus generic proxy handles for sub‑class (dashed) and type (dotted) lines.
"""

from __future__ import annotations

import matplotlib.lines as mlines
import matplotlib.pyplot as plt


def build_proxy_legend(fig: plt.Figure, axes: list[plt.Axes]):
    """Add a legend to ``fig`` that contains class handles and style proxies.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to which the legend will be attached.
    axes : list[matplotlib.axes.Axes]
        List of Axes objects; the function uses the first axis to retrieve the
        class handles.
    """
    class_handles, class_labels = axes[0].get_legend_handles_labels()
    proxy_sub = mlines.Line2D([], [], color='gray', linewidth=1, linestyle='--', label='Sub‑class')
    proxy_type = mlines.Line2D([], [], color='gray', linewidth=1, linestyle=':', label='Type')
    legend_handles = class_handles + [proxy_sub, proxy_type]
    legend_labels = class_labels + [proxy_sub.get_label(), proxy_type.get_label()]
    fig.legend(legend_handles, legend_labels, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=10, frameon=True)
