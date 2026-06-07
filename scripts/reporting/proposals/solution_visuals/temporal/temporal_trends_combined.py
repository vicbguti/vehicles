import os
import sys
import yaml
import matplotlib.pyplot as plt
from glob import glob

# Ensure required package directories are on the Python path for imports
# Add the directory containing the 'temporal' package (solution_visuals) to sys.path
temporal_pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add the top-level utils package (scripts/reporting/utils) to sys.path
utils_pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, temporal_pkg_dir)
sys.path.insert(0, utils_pkg_dir)
# Imports now resolve via absolute package names

# Core utilities
from temporal.core.loader import discover_csv_files, parse_date_column
from temporal.core.aggregator import aggregate_combined
from temporal.core.plotter.combined import plot_combined_grid
import pandas as pd


def main():
    """Generate the combined temporal trends grid chart.

    This function loads configuration, aggregates registration counts per
    province and class (using the dict‑level helper), converts the result to a
    DataFrame, trims trailing zero rows, and delegates plotting to the core
    ``plot_combined_grid`` helper.
    """
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Determine directories
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
    figures_dir = os.path.join(config['paths']['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)

    # Target groups (kept from original script for visual fidelity)
    target_provinces = ['GUAYAS', 'PICHINCHA', 'MANABI', 'AZUAY', 'TUNGURAHUA']
    target_classes = ['MOTOCICLETA', 'JEEP', 'AUTOMOVIL', 'CAMIONETA']

    # Aggregate using the dict‑level helper
    agg_dict = aggregate_combined(base_dir=base_dir, config=config, target_classes=target_classes, target_provinces=target_provinces)

    # Convert dict to DataFrame (mirroring the old combined_df wrapper)
    rows = []
    for (year, month, province, cls), count in agg_dict.items():
        rows.append({
            "year": int(year),
            "month": int(month),
            "province": province,
            "class": cls,
            "count": int(count),
            "date_label": f"{int(year)}-{str(int(month)).zfill(2)}",
        })
    df = pd.DataFrame(rows)
    if df.empty:
        print('No data to plot for the given parameters.')
        return
    # Plot the grid
    out_path = os.path.join(figures_dir, 'temporal_trends_combined.png')
    plot_combined_grid(df, target_provinces, target_classes, out_path)
    print(f"Temporal trends combined chart saved to {out_path}")


if __name__ == '__main__':
    main()
