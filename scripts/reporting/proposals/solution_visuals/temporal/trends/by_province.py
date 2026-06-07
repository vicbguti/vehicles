import os
import yaml
import pandas as pd
from ..base import parse_date, parse_slash_date, trim_zero_tail
from ..core.loader import discover_csv_files, parse_date_column
from ..core.aggregator import aggregate_by_province
from ..core.plotter import apply_trim, plot_time_series


def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
    monthly_counts = aggregate_by_province(base_dir, config)

    # Build DataFrame for plotting
    # Determine unique provinces from keys
    provinces = sorted({prov for (_, _, prov) in monthly_counts.keys()})
    plot_data = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            date_label = f"{year}-{str(month).zfill(2)}"
            row = {'date_label': date_label, 'year': year, 'month': month}
            for prov in provinces:
                row[prov] = monthly_counts.get((year, month, prov), 0)
            plot_data.append(row)
    df_plot = pd.DataFrame(plot_data)
    df_plot = apply_trim(df_plot, date_col='date_label')

    # Plotting – use a colour map generated from Matplotlib's tab20 palette
    import matplotlib.pyplot as _mpl
    cmap = _mpl.cm.get_cmap('tab20')
    colors_map = {prov: cmap(i % 20) for i, prov in enumerate(provinces)}

    figures_dir = os.path.join(config['paths']['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)
    out_path = os.path.join(figures_dir, 'temporal_trends_location.png')
    plot_time_series(
        df=df_plot,
        metric_cols=provinces,
        colors_map=colors_map,
        title='Monthly Vehicle Registration Demand by Province (Ecuador, 2017-2026)',
        ylabel='Registrations (Thousands)',
        out_path=out_path,
        figsize=(14, 7),
    )
    print(f"Temporal trends by province chart saved to {out_path}")
