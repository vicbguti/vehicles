"""Axis helper functions for date formatting.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def format_date_axis(ax: plt.Axes, freq="3M") -> None:
    """Apply auto locator/formatter to X axis.

    Parameters
    ----------
    ax: plt.Axes
        Axis to format.
    freq: str
        Frequency string for locator (e.g., "3M" for every 3 months).
    """
    locator = mdates.AutoDateLocator(minticks=4, maxticks=12)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
