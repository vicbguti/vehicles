import os
import sys
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
import os
import sys
# Ensure utils package is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# Ensure utils package is on path (already added above)
# Imports adjusted for relative package resolution
from utils.date import parse_date, parse_slash_date
from utils.time_series.trimming import trim_zero_tail
from temporal.core.aggregator import aggregate_by_province
from temporal.core.plotter.location import plot_location_grid


def main():
    # Read config for paths
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)
    
    # Target top 5 provinces in Ecuador
    target_provinces = ['GUAYAS', 'PICHINCHA', 'MANABI', 'AZUAY', 'TUNGURAHUA']
    
    # Use core aggregator dict version
    agg_dict = aggregate_by_province(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')), config=config, target_provinces=target_provinces)
    # Convert dict to DataFrame (with columns for each province)
    plot_data = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            date_label = f"{year}-{str(month).zfill(2)}"
            row = {'date_label': date_label, 'year': year, 'month': month}
            for prov in target_provinces:
                row[prov] = agg_dict.get((year, month, prov), 0)
            plot_data.append(row)
    df_plot = pd.DataFrame(plot_data)
    if not df_plot.empty:
        df_plot = df_plot.sort_values(["year", "month"]).reset_index(drop=True)
    df_plot = trim_zero_tail(df_plot, date_col='date_label')
    out_path = os.path.join(figures_dir, 'temporal_trends_location.png')
    plot_location_grid(df_plot, target_provinces, out_path)
    print(f"Temporal trends by location chart saved to {out_path}")

if __name__ == '__main__':
    main()
