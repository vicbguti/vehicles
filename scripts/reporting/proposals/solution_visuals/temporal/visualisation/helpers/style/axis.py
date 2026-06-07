# -*- coding: utf-8 -*-
"""Axis‑level styling utilities for visualisation plotters.

These helpers encapsulate Matplotlib styling concerns such as axis formatting
and applying a consistent look‑and‑feel.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from visualisation.style import format_date_axis

def _apply_style(ax: plt.Axes, title: str) -> None:
    """Apply common styling to an axis.

    Parameters
    ----------
    ax: plt.Axes
        Axis to style.
    title: str
        Title text for the subplot.
    """
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_ylabel("Registrations (k)", fontsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    format_date_axis(ax)
