import os
import sys
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from utils import parse_date, parse_slash_date

def main():
    # Read config for paths
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)
    
    print("Aggregating monthly registration volume...")
    csv_files = sorted(glob(os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['files_pattern'])))
    monthly_counts = {}
    
    for f in csv_files:
        print(f"Reading {os.path.basename(f)}...")
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        
        if '2017' in os.path.basename(f):
            # 2017 uses 'Mes Adquisición' or 'Mes  registro venta'
            col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[col])
            counts = df[col].dropna().value_counts()
            for month, count in counts.items():
                try:
                    m = int(float(month))
                    if 1 <= m <= 12:
                        monthly_counts[(2017, m)] = monthly_counts.get((2017, m), 0) + count
                except ValueError:
                    pass
            continue
            
        # Match process date column dynamically
        date_col = None
        for opt in ['FECHA PROCESO', 'FECHA COMPRA']:
            for c in cols:
                if opt.upper() in c.strip().upper():
                    date_col = c
                    break
            if date_col:
                break
                
        if not date_col:
            print(f"Warning: could not find date column in {os.path.basename(f)}. Available columns: {cols}")
            continue
            
        # Parse dates – handles slash (MM/DD or DD/MM) and Spanish dash (DD-ENE-2021)
        is_mm_dd = 'MM/DD' in date_col
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col])
        dates = df[date_col].dropna().astype(str)

        parsed = dates.apply(lambda v: parse_slash_date(v, is_mm_dd) if '/' in str(v) else parse_date(v))
        years = parsed.apply(lambda t: t[0])
        months = parsed.apply(lambda t: t[1])

        combined = pd.DataFrame({'year': years, 'month': months})
        combined = combined[(combined['month'] >= 1) & (combined['month'] <= 12) & (combined['year'] >= 2017) & (combined['year'] <= 2026)]

        counts = combined.groupby(['year', 'month']).size()
        for (y, m), count in counts.items():
            key = (int(y), int(m))
            monthly_counts[key] = monthly_counts.get(key, 0) + count
            
    # Structure data for plotting
    plot_data = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            count = monthly_counts.get((year, month), 0)
            plot_data.append({
                'date_label': f"{year}-{str(month).zfill(2)}",
                'year': year,
                'month': month,
                'count': count
            })
            
    df_plot = pd.DataFrame(plot_data)
    df_plot = df_plot.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Plotting
    plt.figure(figsize=(12, 6))
    
    # Line plot with modern styling
    plt.plot(df_plot['date_label'], df_plot['count'] / 1000, color='#1d3557', linewidth=2.5, marker='o', markersize=4, label='Registrations')
    
    # Styling and ticks setup
    plt.title('Monthly Vehicle Registration Demand Trends (Ecuador, 2017-2026)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Timeline (Year-Month)', fontsize=11, labelpad=10)
    plt.ylabel('Registrations (Thousands)', fontsize=11, labelpad=10)
    
    # Keep X axis readable by showing tick labels only every 6 months
    tick_positions = range(0, len(df_plot), 6)
    tick_labels = [df_plot['date_label'][i] for i in tick_positions]
    plt.xticks(tick_positions, tick_labels, rotation=45, fontsize=9)
    plt.grid(axis='both', linestyle='--', alpha=0.5)
    
    # Remove top and right spines
    for spine in ['top', 'right']:
        plt.gca().spines[spine].set_visible(False)
        
    plt.tight_layout()
    out_path = os.path.join(figures_dir, 'temporal_trends.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Temporal trends chart saved to {out_path}")

if __name__ == '__main__':
    main()
