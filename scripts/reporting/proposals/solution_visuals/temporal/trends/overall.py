import os
import yaml
import pandas as pd
from ..base import parse_date, parse_slash_date, trim_zero_tail
from ..core.loader import discover_csv_files, parse_date_column
from ..core.aggregator import aggregate_overall
from ..core.plotter import apply_trim, plot_time_series


def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
    monthly_counts = aggregate_overall(base_dir, config)

    # Build DataFrame for plotting
    plot_data = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            count = monthly_counts.get((year, month), 0)
            plot_data.append({
                'date_label': f"{year}-{str(month).zfill(2)}",
                'year': year,
                'month': month,
                'count': count,
            })
    df_plot = pd.DataFrame(plot_data)
    df_plot = apply_trim(df_plot, date_col='date_label')

    # Plotting
    figures_dir = os.path.join(config['paths']['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)
    out_path = os.path.join(figures_dir, 'temporal_trends.png')
    colors_map = {'count': '#1d3557'}
    plot_time_series(
        df=df_plot,
        metric_cols=['count'],
        colors_map=colors_map,
        title='Monthly Vehicle Registration Demand Trends (Ecuador, 2017-2026)',
        ylabel='Registrations (Thousands)',
        out_path=out_path,
        figsize=(12, 6),
    )
    print(f"Temporal trends chart saved to {out_path}")
