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
    data_dict_path = os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['dictionary'])
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'temporal')
    os.makedirs(figures_dir, exist_ok=True)
    
    print("Loading canton catalog to map provinces...")
    df_cat = pd.read_excel(data_dict_path, sheet_name='Catálogo_Cantones', skiprows=1)
    df_cat.columns = ['canton_code', 'canton_desc', 'province_code', 'province_desc']
    
    canton_to_province = {}
    for _, row in df_cat.iterrows():
        c_code = row['canton_code']
        p_desc = row['province_desc']
        if pd.notnull(c_code) and pd.notnull(p_desc):
            try:
                c_code_str = str(int(float(c_code))).strip()
                canton_to_province[c_code_str] = str(p_desc).strip().upper()
            except ValueError:
                pass

    print("Aggregating monthly registration volume per province and class...")
    csv_files = sorted(glob(os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['files_pattern'])))
    monthly_combined_counts = {}
    
    # Target groups
    target_provinces = ['GUAYAS', 'PICHINCHA', 'MANABI', 'AZUAY', 'TUNGURAHUA']
    target_classes = ['MOTOCICLETA', 'JEEP', 'AUTOMOVIL', 'CAMIONETA']
    
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
                
        # Match canton column dynamically
        canton_col = None
        for opt in ['CANTÓN', 'CANTON', 'Codigo Canton', 'Canton', 'CÓDIGO CANTON']:
            for c in cols:
                if c.strip().upper() == opt.upper():
                    canton_col = c
                    break
            if canton_col:
                break
                
        if not class_col or not canton_col:
            print(f"Warning: missing columns in {os.path.basename(f)}.")
            continue
            
        if '2017' in os.path.basename(f):
            # 2017 uses 'Mes Adquisición' or 'Mes  registro venta'
            date_col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, canton_col, class_col])
            df = df.dropna(subset=[date_col, canton_col, class_col])
            
            counts = df.groupby([date_col, canton_col, class_col]).size()
            for (month, canton, cl), count in counts.items():
                try:
                    m = int(float(month))
                    c_str = str(int(float(canton))).strip()
                    prov = canton_to_province.get(c_str)
                    cl_upper = str(cl).strip().upper()
                    if 1 <= m <= 12 and prov in target_provinces and cl_upper in target_classes:
                        key = (2017, m, prov, cl_upper)
                        monthly_combined_counts[key] = monthly_combined_counts.get(key, 0) + count
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
            print(f"Warning: could not find date column in {os.path.basename(f)}.")
            continue
            
        # Parse dates – handles slash (MM/DD or DD/MM) and Spanish dash (DD-ENE-2021)
        is_mm_dd = 'MM/DD' in date_col
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, canton_col, class_col])
        df = df.dropna(subset=[date_col, canton_col, class_col])
        dates = df[date_col].astype(str)

        parsed = dates.apply(lambda v: parse_slash_date(v, is_mm_dd) if '/' in str(v) else parse_date(v))
        df['year'] = parsed.apply(lambda t: t[0])
        df['month'] = parsed.apply(lambda t: t[1])
        
        # Map canton to province
        df['canton_str'] = df[canton_col].apply(lambda x: str(int(float(x))).strip() if pd.notnull(x) else "")
        df['province'] = df['canton_str'].map(canton_to_province)
        
        combined = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]
        
        counts = combined.groupby(['year', 'month', 'province', class_col]).size()
        for (y, m, prov, cl), count in counts.items():
            prov_upper = str(prov).strip().upper()
            cl_upper = str(cl).strip().upper()
            if prov_upper in target_provinces and cl_upper in target_classes:
                key = (int(y), int(m), prov_upper, cl_upper)
                monthly_combined_counts[key] = monthly_combined_counts.get(key, 0) + count
                
    # Prepare data structure for plotting
    timeline = []
    for year in range(2017, 2027):
        for month in range(1, 13):
            timeline.append((year, month, f"{year}-{str(month).zfill(2)}"))
            
    # Plotting: Faceted 2x3 Grid
    fig, axes = plt.subplots(2, 3, figsize=(20, 12), sharex=True)
    axes = axes.flatten()
    
    colors_map = {
        'MOTOCICLETA': '#e63946',
        'JEEP': '#1d3557',
        'AUTOMOVIL': '#457b9d',
        'CAMIONETA': '#ffb703'
    }
    
    # Keep X axis labels clean
    tick_positions = range(0, len(timeline), 12)
    tick_labels = [timeline[i][2] for i in tick_positions]
    
    for idx, prov in enumerate(target_provinces):
        ax = axes[idx]
        for cl in target_classes:
            y_values = [monthly_combined_counts.get((y, m, prov, cl), 0) / 1000 for y, m, _ in timeline]
            ax.plot(range(len(timeline)), y_values, color=colors_map[cl], linewidth=1.8, label=cl)
            
        ax.set_title(f"Province: {prov}", fontsize=12, fontweight='bold')
        ax.grid(axis='both', linestyle='--', alpha=0.5)
        ax.set_ylabel('Registrations (k)', fontsize=10)
        
        # Remove spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
            
    # The 6th plot serves as a consolidated legend panel
    ax_legend = axes[5]
    ax_legend.axis('off')
    # Build a legend on the empty axis
    handles = [plt.Line2D([0], [0], color=colors_map[cl], lw=3, label=cl) for cl in target_classes]
    ax_legend.legend(handles=handles, loc='center', frameon=True, fontsize=14, title='Vehicle Classes', title_fontsize=16)
    
    # Apply tick labels to the bottom subplots
    for i in [3, 4]:
        axes[i].set_xticks(tick_positions)
        axes[i].set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=9)
        axes[i].set_xlabel('Timeline (Year-Month)', fontsize=11)
        
    plt.suptitle('Monthly Vehicle Registration Trends by Province and Class (Ecuador, 2017-2026)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    out_path = os.path.join(figures_dir, 'temporal_trends_combined.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Combined temporal trends grid chart saved to {out_path}")

if __name__ == '__main__':
    main()
