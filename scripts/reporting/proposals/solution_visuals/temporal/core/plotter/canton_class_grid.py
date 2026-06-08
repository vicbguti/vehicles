import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from ..style import apply_style
import matplotlib.lines as mlines
from utils.geo_mapper.mapper import code_to_name


def plot_canton_class_grid(df: pd.DataFrame,
                           cantons: list | None,
                           out_path: str) -> None:
    """Create a facet grid of temporal trends for each canton.

    Parameters
    ----------
    df : pd.DataFrame
        Expected columns: 'date_label', 'canton', 'class', 'sub_class', 'type', 'count'.
    cantons : list | None
        List of canton codes/names to plot. If ``None`` all cantons in ``df`` are used.
    out_path : str
        Destination file path for the PNG image.
    """
    # Filter cantons if a list is provided
    if cantons is not None:
        df = df[df['canton'].isin(cantons)]
    if df.empty:
        raise ValueError("No data available for the selected cantons.")

    # Determine unique cantons and limit layout size (max 12 per page)
    unique_cantons = sorted(df['canton'].unique())
    # Choose a grid size that is roughly square
    n = len(unique_cantons)
    ncols = min(4, n)
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), sharex=True, sharey=True)
    # Flatten for easy iteration (handles case of single row/col)
    axes = axes.flatten() if isinstance(axes, (list, np.ndarray)) else [axes]

    # Define a premium colour map per vehicle class
    class_colors = {
        'MOTOCICLETA': '#e63946',
        'JEEP': '#1d3557',
        'AUTOMOVIL': '#457b9d',
        'CAMIONETA': '#ffb703',
        'CAMON': '#8d99ae'
    }
    # Fallback colour
    fallback_color = '#6a994e'

    # Prepare date axis
    unique_dates = sorted(df['date_label'].unique())
    plot_dates = pd.to_datetime(unique_dates)

    # Plot each canton on its own axis
for ax, canton in zip(axes, unique_cantons):
    sub_df = df[df['canton'] == canton]

    # Plot class lines (solid, visible)
    for cls in sub_df['class'].unique():
        cls_df = sub_df[sub_df['class'] == cls]
        series = cls_df.groupby('date_label')['count'].sum().reindex(plot_dates, fill_value=0)
        color = class_colors.get(cls, fallback_color)
        ax.plot(plot_dates, series / 1000, label=cls, color=color, linewidth=2.0, linestyle='-')

    # Plot Sub‑class trends (dashed, hidden labels)
    if 'sub_class' in sub_df.columns:
        for sub_class in sub_df['sub_class'].unique():
            sc_df = sub_df[sub_df['sub_class'] == sub_class]
            series_sc = sc_df.groupby('date_label')['count'].sum().reindex(plot_dates, fill_value=0)
            ax.plot(plot_dates, series_sc / 1000, color='gray', linewidth=1.0, linestyle='--', label='_nolegend_')

    # Plot Type trends (dotted, hidden labels)
    if 'type' in sub_df.columns:
        for typ in sub_df['type'].unique():
            typ_df = sub_df[sub_df['type'] == typ]
            series_typ = typ_df.groupby('date_label')['count'].sum().reindex(plot_dates, fill_value=0)
            ax.plot(plot_dates, series_typ / 1000, color='gray', linewidth=1.0, linestyle=':', label='_nolegend_')

    canton_name = code_to_name(str(canton)) or str(canton)
    ax.set_title(f"Canton: {canton_name}", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_ylabel('Registrations (k)', fontsize=9)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    # Hide any unused axes
    for i in range(len(unique_cantons), len(axes)):
        axes[i].axis('off')
# No extra plotting needed for hidden axes
    # Global legend – class handles + generic style proxies
    class_handles, class_labels = axes[0].get_legend_handles_labels()
    proxy_sub = mlines.Line2D([], [], color='gray', linewidth=1, linestyle='--', label='Sub‑class')
    proxy_type = mlines.Line2D([], [], color='gray', linewidth=1, linestyle=':', label='Type')
    legend_handles = class_handles + [proxy_sub, proxy_type]
    legend_labels = class_labels + [proxy_sub.get_label(), proxy_type.get_label()]
    fig.legend(legend_handles, legend_labels, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=10, frameon=True)

    # X‑axis tick formatting – show one tick per year for readability
    tick_positions = range(0, len(df['date_label'].unique()), 12)
    tick_labels = [df['date_label'].unique()[i] for i in tick_positions]
    plt.xticks(tick_positions, tick_labels, rotation=45, fontsize=8)

    # Apply consistent premium style
    # Apply a consistent premium style to the figure (optional)
# apply_style(fig, title='Monthly Vehicle Registrations by Canton, Class, Sub‑Class & Type (2017‑2026)',
#             ylabel='Registrations (Thousands)')

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Canton‑class visual saved to {out_path}")
