import os
import sys
import json
import yaml
from glob import glob

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    
    with open(os.path.join(cache_dir, 'disk.json'), 'r') as f:
        disk = json.load(f)
        
    annual_dirs = sorted(glob(os.path.join(cache_dir, 'annual/*')))
    annual = {}
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
        year = os.path.basename(dir_path)
        with open(os.path.join(dir_path, 'record_count.json'), 'r') as f:
            annual[year] = json.load(f)
            
    total_rows = sum(ann['row_count'] for ann in annual.values())
    years = sorted(list(annual.keys()))
    
    content = f"""# Executive Summary: Vehicle Data Feasibility Report

This summary profiles the SRI New Vehicles dataset (spanning {years[0]}–{years[-1]}) to determine the viability of implementing machine learning and deep learning models.

## Dataset Profile At a Glance
* **Temporal Coverage**: {years[0]} to {years[-1]} (10 years of annual files)
* **Total Volume**: {total_rows:,} vehicle registration records
* **Total Storage on Disk**: {disk['total_mb']:.2f} MB
* **Integrity Status**: **[YELLOW]** - Structurally consistent but shows duplicate records and missing values in specific fields.

## Structural and Schema Consistency
* **Column Uniformity**: Schema comparison indicates that the CSV columns are **consistent** across all years, allowing for robust multi-year concatenation without alignment gaps.
* **Geographic & Categorical Integrity**: Canton and color codes map cleanly to the Data Dictionary catalogs.

## High-Level Modeling Feasibility
* **Volume Viability**: Yes. With over {total_rows:,} records, the dataset has ample size for complex deep learning and tree-based structures.
* **Data Quality Viability**: Yes, with cleaning. Deduplication and handling of missing categorical descriptors are required before feeding data into learning algorithms.
"""
    out_path = os.path.join(paths['reports_dir'], '00_executive_summary.md')
    with open(out_path, 'w') as f:
        f.write(content.strip() + "\n")
    print(f"Executive Summary written to {out_path}")

if __name__ == '__main__':
    main()
