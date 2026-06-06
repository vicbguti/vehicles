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
    
    print("Aggregating monthly registration volume per vehicle class...")
    csv_files = sorted(glob(os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['files_pattern'])))
    monthly_class_counts = {}
    
    # Top classes to track (maps to catalog names)
    target_classes = ['MOTOCICLETA', 'JEEP', 'AUTOMOVIL', 'CAMIONETA', 'CAMION']
    
    for f in csv_files:
        print(f"Reading {os.path.basename(f)}...")
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        
        # Match class column dynamically
        class_col = None
        for opt in ['CLASE', 'Clase']:
            for c in cols:
                if c.strip().upper() == opt.upper():
                    class_col = c
                    break
            if class_col:
                break
                
        if not class_col:
            print(f"Warning: could not find class column in {os.path.basename(f)}.")
            continue
            
        if '2017' in os.path.basename(f):
            # 2017 uses 'Mes Adquisición' or 'Mes  registro venta'
            date_col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, class_col])
            df = df.dropna(subset=[date_col, class_col])
            
            counts = df.groupby([date_col, class_col]).size()
            for (month, cl), count in counts.items():
                try:
                    m = int(float(month))
                    cl_upper = str(cl).strip().upper()
                    if 1 <= m <= 12 and cl_upper in target_classes:
                        key = (2017, m, cl_upper)
                        monthly_class_counts[key] = monthly_class_counts.get(key, 0) + count
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
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, class_col])
        df = df.dropna(subset=[date_col, class_col])
        dates = df[date_col].astype(str)

        parsed = dates.apply(lambda v: parse_slash_date(v, is_mm_dd) if '/' in str(v) else parse_date(v))
        df['year'] = parsed.apply(lambda t: t[0])
        df['month'] = parsed.apply(lambda t: t[1])

        combined = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]
        
        counts = combined.groupby(['year', 'month', class_col]).size()
        for (y, m, cl), count in counts.items():
            cl_upper = str(cl).strip().upper()
            if cl_upper in target_classes:
                key = (int(y), int(m), cl_upper)
                monthly_class_counts[key] = monthly_class_counts.get(key, 0) + count
                
    # Structure data for plotting
    plot_data = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            date_label = f"{year}-{str(month).zfill(2)}"
            row = {'date_label': date_label, 'year': year, 'month': month}
            for cl in target_classes:
                row[cl] = monthly_class_counts.get((year, month, cl), 0)
            plot_data.append(row)
            
    df_plot = pd.DataFrame(plot_data)
    df_plot = df_plot.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Plotting
    plt.figure(figsize=(14, 7))
    
    # Premium colors for classes
    colors_map = {
        'MOTOCICLETA': '#e63946',
        'JEEP': '#1d3557',
        'AUTOMOVIL': '#457b9d',
        'CAMIONETA': '#ffb703',
        'CAMION': '#8d99ae'
    }
    
    for cl in target_classes:
        plt.plot(df_plot['date_label'], df_plot[cl] / 1000, color=colors_map[cl], linewidth=2.0, marker='o', markersize=3, label=cl)
        
    # Styling and ticks setup
    plt.title('Monthly Vehicle Registration Demand by Class (Ecuador, 2017-2026)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Timeline (Year-Month)', fontsize=11, labelpad=10)
    plt.ylabel('Registrations (Thousands)', fontsize=11, labelpad=10)
    
    # Keep X axis readable by showing tick labels only every 6 months
    tick_positions = range(0, len(df_plot), 6)
    tick_labels = [df_plot['date_label'][i] for i in tick_positions]
    plt.xticks(tick_positions, tick_labels, rotation=45, fontsize=9)
    plt.grid(axis='both', linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=10)
    
    # Remove top and right spines
    for spine in ['top', 'right']:
        plt.gca().spines[spine].set_visible(False)
        
    plt.tight_layout()
    out_path = os.path.join(figures_dir, 'temporal_trends_class.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Temporal trends by class chart saved to {out_path}")

if __name__ == '__main__':
    main()
