import os
import sys
import yaml
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob

# Base coordinate centroids for Ecuador provinces to map demands geographically
PROVINCE_COORDS = {
    201: (-2.900, -79.005),  # AZUAY
    202: (-1.590, -79.000),  # BOLIVAR
    203: (-2.740, -78.840),  # CAÑAR
    204: (0.812, -77.717),   # CARCHI
    205: (-0.933, -78.614),  # COTOPAXI
    206: (-1.673, -78.648),  # CHIMBORAZO
    107: (-3.258, -79.955),  # EL ORO
    108: (0.959, -79.654),   # ESMERALDAS
    420: (-0.900, -89.600),  # GALAPAGOS
    109: (-2.189, -79.889),  # GUAYAS
    210: (0.351, -78.118),   # IMBABURA
    211: (-3.993, -79.204),  # LOJA
    112: (-1.802, -79.534),  # LOS RIOS
    113: (-1.055, -80.454),  # MANABI
    314: (-2.308, -78.118),  # MORONA SANTIAGO
    315: (-0.994, -77.813),  # NAPO
    322: (-0.466, -76.987),  # ORELLANA
    316: (-1.484, -78.002),  # PASTAZA
    217: (-0.181, -78.468),  # PICHINCHA
    124: (-2.227, -80.858),  # SANTA ELENA
    223: (-0.253, -79.175),  # SANTO DOMINGO DE LOS TSÁCHILAS
    321: (0.084, -76.883),   # SUCUMBIOS
    218: (-1.249, -78.627),  # TUNGURAHUA
    319: (-4.069, -78.957),  # ZAMORA CHINCHIPE
}

def main():
    # Read config for paths
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    data_dict_path = os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['dictionary'])
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'spatial')
    os.makedirs(figures_dir, exist_ok=True)
    
    print("Loading canton catalog sheet...")
    # Load canton catalog to map canton code -> province code and name
    df_cat = pd.read_excel(data_dict_path, sheet_name='Catálogo_Cantones', skiprows=1)
    df_cat.columns = ['canton_code', 'canton_desc', 'province_code', 'province_desc']
    
    canton_map = {}
    for _, row in df_cat.iterrows():
        c_code = row['canton_code']
        p_code = row['province_code']
        c_desc = row['canton_desc']
        if pd.notnull(c_code) and pd.notnull(p_code):
            try:
                c_code_str = str(int(float(c_code))).strip()
                p_code_int = int(float(p_code))
                canton_map[c_code_str] = (p_code_int, str(c_desc).strip())
            except ValueError:
                pass
                
    print("Aggregating canton demand across registrations...")
    csv_files = sorted(glob(os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['files_pattern'])))
    canton_counts = {}
    
    for f in csv_files:
        print(f"Reading {os.path.basename(f)}...")
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        
        # Match canton column dynamically to resolve schema variance across years
        canton_col = None
        for opt in ['CANTÓN', 'CANTON', 'Codigo Canton', 'Canton', 'CÓDIGO CANTON']:
            for c in cols:
                if c.strip().upper() == opt.upper():
                    canton_col = c
                    break
            if canton_col:
                break
                
        if not canton_col:
            print(f"Warning: could not find canton column in {os.path.basename(f)}. Available columns: {cols}")
            continue
            
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[canton_col])
        for val, count in df[canton_col].value_counts().items():
            try:
                val_str = str(int(float(val))).strip()
                canton_counts[val_str] = canton_counts.get(val_str, 0) + count
            except ValueError:
                pass
                
    # Build plotting dataframe
    plot_data = []
    for c_code, count in canton_counts.items():
        if c_code in canton_map:
            p_code, name = canton_map[c_code]
            if p_code in PROVINCE_COORDS:
                base_lat, base_lon = PROVINCE_COORDS[p_code]
                
                # Jitter offset based on the hash of canton code to spread out overlapping cantons within a province
                h = hash(c_code)
                jitter_lat = ((h % 100) - 50) / 300.0
                jitter_lon = (((h // 100) % 100) - 50) / 300.0
                
                plot_data.append({
                    'canton_code': c_code,
                    'name': name,
                    'lat': base_lat + jitter_lat,
                    'lon': base_lon + jitter_lon,
                    'demand': count
                })
                
    if not plot_data:
        print("Error: No plotting data constructed.")
        return
        
    df_plot = pd.DataFrame(plot_data)
    
    # Plotting
    plt.figure(figsize=(10, 8))
    
    # Scatter bubble plot
    sc = plt.scatter(
        df_plot['lon'], df_plot['lat'],
        s=np.sqrt(df_plot['demand']) * 2.0,
        c=df_plot['demand'] / 1000,
        cmap='viridis',
        alpha=0.75,
        edgecolors='none'
    )
    
    # Add a premium colorbar
    cb = plt.colorbar(sc, pad=0.02)
    cb.set_label('Demand Volume (Thousands of Registrations)', fontsize=11, labelpad=10)
    cb.ax.tick_params(labelsize=9)
    
    # Annotate top 10 cantons with box labels
    top_10 = df_plot.nlargest(10, 'demand')
    for idx, row in top_10.iterrows():
        plt.annotate(
            row['name'],
            (row['lon'], row['lat']),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center',
            fontsize=8,
            fontweight='bold',
            color='#1d3557',
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#457b9d", lw=0.5, alpha=0.85)
        )
        
    plt.title('Geographic Vehicle Registration Demand (Ecuador)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Longitude', fontsize=11, labelpad=10)
    plt.ylabel('Latitude', fontsize=11, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Focus coordinate limits on mainland Ecuador
    plt.xlim(-81.5, -75.0)
    plt.ylim(-5.2, 1.8)
    
    # Remove top and right spines
    for spine in ['top', 'right']:
        plt.gca().spines[spine].set_visible(False)
        
    plt.tight_layout()
    out_path = os.path.join(figures_dir, 'geographic_demands.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Geographic demands chart saved to {out_path}")

if __name__ == '__main__':
    main()
