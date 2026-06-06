import os
import sys

# Add project root to sys.path so that imports from `scripts.reporting.utils` work when running the script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import yaml
import glob

from scripts.reporting.utils.column_finder import find_column
from scripts.reporting.utils.visual_helpers import apply_style, save_figure

def main():
    # Load configuration for paths
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    figures_dir = os.path.join(project_root, cfg['paths']['reports_dir'], 'figures', 'proposals', 'subclass_type')
    os.makedirs(figures_dir, exist_ok=True)

    # Find all raw CSV files matching the pattern
    csv_pattern = os.path.join(project_root, cfg['data']['files_pattern'])
    csv_files = sorted(glob.glob(csv_pattern))

    # Aggregation dictionary: (subclass, class) -> count
    agg = {}
    for f in csv_files:
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        class_col = find_column(cols, ['CLASE', 'Clase'], exact=True)
        subclass_col = find_column(cols, ['SUB CLASE', 'SUB_CLASE', 'SUBCLASE'], exact=True)
        if not class_col or not subclass_col:
            continue
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[class_col, subclass_col])
        df = df.dropna(subset=[class_col, subclass_col])
        counts = df.groupby([class_col, subclass_col]).size()
        for (cl, sub), cnt in counts.items():
            key = (str(cl).strip().upper(), str(sub).strip().upper())
            agg[key] = agg.get(key, 0) + cnt

    if not agg:
        print('No subclass data aggregated – nothing to plot.')
        return

    classes = sorted({k[0] for k in agg.keys()})
    subclasses = sorted({k[1] for k in agg.keys()})
    data = pd.DataFrame(0, index=classes, columns=subclasses)
    for (cl, sub), cnt in agg.items():
        data.at[cl, sub] = cnt

    # Apply visual style (defined in visual_helpers)
    apply_style()
    plt.figure(figsize=(12, 8))
    sns.heatmap(data, cmap='viridis', linewidths=0.5, annot=False)
    plt.title('Vehicle Registrations – Class vs. Subclass (2017‑2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Subclass')
    plt.ylabel('Vehicle Class')
    plt.tight_layout()
    out_path = os.path.join(figures_dir, 'subclass_matrix.png')
    save_figure(out_path)
    plt.close()
    print(f'Subclass matrix chart saved to {out_path}')

if __name__ == '__main__':
    main()
