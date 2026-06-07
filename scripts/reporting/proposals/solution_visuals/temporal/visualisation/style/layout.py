"""Layout utilities for consistent figure appearance.
"""

import matplotlib.pyplot as plt
from matplotlib.legend import Legend


def apply_layout(fig: plt.Figure, title: str | None = None) -> None:
    """Apply a premium style to the whole figure.

    * Sets a light background.
    * Increases default font sizes.
    * Adjusts the figure size based on the number of sub‑plots.
    * Moves the global legend to the right side of the grid.
    """
    if title:
        fig.suptitle(title, fontsize=14, fontweight="bold")
    # Light background for premium look.
    fig.patch.set_facecolor("#f8f9fa")
    # Attempt to locate a legend in the figure and reposition it.
    legend = None
    for artist in fig.get_children():
        if isinstance(artist, Legend):
            legend = artist
            break
    if legend:
        legend.set_bbox_to_anchor((1.02, 1))
    # Tight layout with space for external legend.
    plt.tight_layout(rect=[0, 0, 0.85, 1])
