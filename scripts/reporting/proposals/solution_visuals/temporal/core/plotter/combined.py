'''Plotting helpers for temporal visualisation.

The functions here are deliberately lightweight and only depend on pandas and
matplotlib. They expect a tidy DataFrame with a ``date_label`` column (YYYY-MM)
and a ``count`` column for each (province, class) combination.
'''

import matplotlib.pyplot as plt
import pandas as pd

from utils.time_series.trimming import trim_zero_tail

def apply_trim(df: pd.DataFrame, date_col: str = "date_label", exclude_cols: list | None = None) -> pd.DataFrame:
    """Trim trailing rows where all metric columns are zero.

    This wrapper forwards ``exclude_cols`` to the shared ``trim_zero_tail`` helper so
    that callers can specify which columns (e.g. ``year``, ``month``, ``province``, ``class``)
    should be ignored when detecting all‑zero rows.
    """
    return trim_zero_tail(df, date_col=date_col, exclude_cols=exclude_cols)


def plot_combined_grid(df: pd.DataFrame, provinces: list, classes: list, out_path: str) -> None:
    """Create the 2×3 faceted grid used for the combined temporal visual.

    Parameters
    ----------
    df: pd.DataFrame
        Must contain columns ``year``, ``month``, ``province``, ``class``,
        ``count`` and ``date_label`` (YYYY‑MM).
    provinces: list
        Ordered list of provinces to plot (matches the original script).
    classes: list
        Ordered list of vehicle classes to plot.
    out_path: str
        Destination file path for the PNG image.
    """
    # Ensure the DataFrame is trimmed before plotting.
    df = apply_trim(df, date_col="date_label", exclude_cols=["year", "month", "province", "class"])

    # Prepare a full timeline for consistent x‑axis across all sub‑plots.
    timeline = []
    max_year = df['year'].max()
    max_month = df[df['year'] == max_year]['month'].max()
    for year in range(df['year'].min(), max_year + 1):
        month_limit = max_month if year == max_year else 12
        for month in range(1, month_limit + 1):
            timeline.append((year, month, f"{year}-{str(month).zfill(2)}"))
    # Build a lookup for quick access.
    timeline_labels = [lbl for _, _, lbl in timeline]

    fig, axes = plt.subplots(2, 3, figsize=(20, 12), sharex=True)
    axes = axes.flatten()

    colors_map = {
        "MOTOCICLETA": "#e63946",
        "JEEP": "#1d3557",
        "AUTOMOVIL": "#457b9d",
        "CAMIONETA": "#ffb703",
    }

    # Plot each province.
    for idx, prov in enumerate(provinces):
        ax = axes[idx]
        for cl in classes:
            # Pull the series for this (prov, cl) across the full timeline.
            mask = (df['province'] == prov) & (df['class'] == cl)
            series = df[mask].set_index('date_label')['count']
            y_vals = [series.get(lbl, 0) / 1000 for lbl in timeline_labels]
            ax.plot(range(len(timeline_labels)), y_vals,
                    color=colors_map.get(cl, "#333"), linewidth=1.8, label=cl)
        ax.set_title(f"Provincia: {prov}", fontsize=12, fontweight="bold")
        ax.grid(axis='both', linestyle='--', alpha=0.5)
        ax.set_ylabel('Registros (k)', fontsize=10)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

    # Legend panel on the 6th axis.
    ax_legend = axes[5]
    ax_legend.axis('off')
    handles = [plt.Line2D([0], [0], color=colors_map.get(cl, "#333"), lw=3, label=cl) for cl in classes]
    ax_legend.legend(handles=handles, loc='center', frameon=True,
                     fontsize=14, title='Clases de Vehículos', title_fontsize=16)

    # X‑axis tick labels – show one tick per year for readability.
    tick_positions = list(range(0, len(timeline_labels), 12))
    tick_labels = [timeline_labels[i] for i in tick_positions]
    for i in [3, 4]:
        axes[i].set_xticks(tick_positions)
        axes[i].set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=9)
        axes[i].set_xlabel('Cronología (Año‑Mes)', fontsize=11)

    plt.suptitle('Tendencias Mensuales de Registro de Vehículos por Provincia y Clase (Ecuador, 2017‑2026)',
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

    print(f"Gráfico combinado de tendencias temporales guardado en {out_path}")
