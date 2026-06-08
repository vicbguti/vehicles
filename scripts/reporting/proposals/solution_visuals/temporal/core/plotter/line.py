import os
import matplotlib.pyplot as plt
from ..style import apply_style
from ..utils import generate_ticks


def plot_time_series(df, metric_cols, colors_map, title, ylabel, out_path, figsize=(14, 7)):
    """Generic line‑plot for a set of metric columns.
    *df* must contain a 'date_label' column for the x‑axis.
    *metric_cols* is an ordered list of column names to plot.
    *colors_map* maps each column to a hex colour.
    """
    fig, ax = plt.subplots(figsize=figsize)
    for col in metric_cols:
        ax.plot(df['date_label'], df[col] / 1000, color=colors_map.get(col, '#333'), linewidth=2.0, marker='o', markersize=3, label=col)
    # Styling
    apply_style(ax, title, ylabel)
    # Tick handling
    positions, labels = generate_ticks(df, step=6)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, fontsize=9)
    # Legend
    ax.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
