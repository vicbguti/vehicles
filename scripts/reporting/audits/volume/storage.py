import os
import json
import yaml
from glob import glob

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    out_dir = os.path.join(paths['reports_dir'], '02_volume')
    os.makedirs(out_dir, exist_ok=True)
    
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
            
    disk_table = "| File Name | Size (MB) | Loaded Rows |\n|---|---|---|\n"
    for f_disk in disk['files']:
        y_str = "".join([c for c in f_disk['file_name'] if c.isdigit()])
        row_count = annual[y_str]['row_count'] if y_str in annual else 0
        disk_table += f"| {f_disk['file_name']} | {f_disk['size_mb']:.2f} MB | {row_count:,} |\n"

    content = f"""# Physical Storage Footprint

This document profiles the physical size, file structure, and disk footprints of the raw dataset.

## 1. Physical storage on Disk
The raw dataset comprises {disk['total_files']} annual CSV files, totaling **{disk['total_mb']:.2f} MB** on disk.

## 2. File-by-File Breakdown
{disk_table}
"""
    out_path = os.path.join(out_dir, 'storage.md')
    with open(out_path, 'w') as f:
        f.write(content.strip() + "\n")
    print(f"Storage Audit Report written to {out_path}")

if __name__ == '__main__':
    main()
