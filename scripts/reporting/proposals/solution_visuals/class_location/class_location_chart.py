import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob
from scripts.reporting.utils import code_to_name, code_to_province
from scripts.reporting.utils.column_finder import find_column

def main():
    # Load configuration for paths
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    paths = config['paths']
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'class_location')
    os.makedirs(figures_dir, exist_ok=True)

    csv_pattern = os.path.join(os.path.dirname(__file__), '../../../../../', config['data']['files_pattern'])
    csv_files = sorted(glob(csv_pattern))

    agg = {}
    for f in csv_files:
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()

        class_col = find_column(cols, ['CLASE', 'Clase'], exact=True)
        if not class_col:
            print(f"Warning: class column not found in {os.path.basename(f)}")
            continue

        loc_col = find_column(cols, ['PROVINCIA', 'CANTON', 'CANTÓN'])
        if not loc_col:
            print(f"Warning: location column not found in {os.path.basename(f)}")
            continue

        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[class_col, loc_col])
        df = df.dropna(subset=[class_col, loc_col])
        # Map location code to province name (fallback to canton name)
        df[loc_col] = df[loc_col].astype(str).apply(
            lambda x: code_to_province(x.strip()) or code_to_name(x.strip()) or x
        )
        counts = df.groupby([class_col, loc_col]).size()
        for (cl, loc), cnt in counts.items():
            loc_str = str(loc).strip().upper()
            if loc_str.isdigit():
                continue
            key = (str(cl).strip().upper(), loc_str)
            agg[key] = agg.get(key, 0) + cnt

        out_path = os.path.join(figures_dir, 'class_location_province_matrix.png')

    if not agg:
        print('No hay datos agregados – nada que plotear.')
        return

    classes = sorted({k[0] for k in agg.keys()})
    locations = sorted({k[1] for k in agg.keys()})
    data = pd.DataFrame(0, index=classes, columns=locations)
    for (cl, loc), cnt in agg.items():
        data.at[cl, loc] = cnt

    from matplotlib.colors import LogNorm
    import matplotlib.ticker as ticker
    plt.figure(figsize=(14, 8))
    # Using LogNorm with vmin=1 so that 0 counts map below the scale, and we color them as the lowest value or mask them.
    # LogNorm shows log-scale colorbar but the actual counts are labeled on it.
    sns.heatmap(
        data, 
        norm=LogNorm(vmin=1, vmax=data.max().max()), 
        cmap='viridis', 
        linewidths=0.5, 
        annot=False,
        cbar_kws={'label': 'Recuento de Registros (k)', 'format': ticker.FuncFormatter(lambda x, _: f"{int(x/1000)}k")}
    )
    plt.title('Registros de Vehículos – Clase vs. Provincia (2017‑2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Provincia')
    plt.ylabel('Clase de Vehículo')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Matriz de Clase‑Provincia guardada en {out_path}")

if __name__ == '__main__':
    main()