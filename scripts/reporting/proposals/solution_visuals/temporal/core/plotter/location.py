import matplotlib.pyplot as plt
from ..style import apply_style

def plot_location_grid(df, provinces, out_path):
    """Plot vehicle registrations per province over time.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with columns ``date_label`` and one column per province containing registration counts.
    provinces : list of str
        List of province names to plot (must match column names in ``df``).
    out_path : str
        File path where the PNG image will be saved.
    """
    # Ensure the DataFrame is sorted by date_label for proper line continuity
    df = df.sort_values('date_label')

    plt.figure(figsize=(14, 7))
    # Define a premium colour map (same as used in the original script)
    colors_map = {
        'GUAYAS': '#e63946',
        'PICHINCHA': '#1d3557',
        'MANABI': '#457b9d',
        'AZUAY': '#ffb703',
        'TUNGURAHUA': '#8d99ae'
    }
    for prov in provinces:
        if prov not in df.columns:
            continue
        plt.plot(df['date_label'], df[prov] / 1000, color=colors_map.get(prov, '#333333'),
                 linewidth=2.0, marker='o', markersize=3, label=prov)

    # Apply consistent style
    ax = plt.gca()
    apply_style(ax,
                title='Monthly Vehicle Registration Demand by Province (Ecuador, 2017-2026)',
                ylabel='Registrations (Thousands)')
    plt.xlabel('Timeline (Year-Month)', fontsize=11, labelpad=10)
    # Show x‑ticks every 6 months for readability
    tick_positions = range(0, len(df), 6)
    tick_labels = [df['date_label'].iloc[i] for i in tick_positions]
    plt.xticks(tick_positions, tick_labels, rotation=45, fontsize=9)
    plt.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
