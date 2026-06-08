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
    
    with open(os.path.join(cache_dir, 'growth.json'), 'r') as f:
        growth = json.load(f)
        
    annual_dirs = sorted(glob(os.path.join(cache_dir, 'annual/*')))
    annual = {}
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
        year = os.path.basename(dir_path)
        with open(os.path.join(dir_path, 'record_count.json'), 'r') as f:
            annual[year] = json.load(f)
            
    years = sorted(list(annual.keys()))
    
    growth_table = "| Period | Record Count | YoY Growth (Abs) | YoY Growth (%) |\n|---|---|---|---|\n"
    growth_map = {g['to_year']: g for g in growth}
    
    for year in years:
        count = annual[year]['row_count']
        if year in growth_map:
            g = growth_map[year]
            abs_chg = f"{g['absolute_change']:+d}"
            pct_chg = f"{g['growth_rate_percentage']:.2f}%"
        else:
            abs_chg = "-"
            pct_chg = "-"
        growth_table += f"| {year} | {count:,} | {abs_chg} | {pct_chg} |\n"

    content = f"""# Temporal Volume & Growth Trends

This report analyzes the annual registration volume trends and year-over-year (YoY) growth of the dataset.

## 1. YoY Growth Table
{growth_table}

## 2. Volume Trend Visualization
The following figure illustrates the registration volumes over the last 10 years:

![Temporal Volume & Growth Trends](../figures/volume_trends.png)
"""
    out_path = os.path.join(out_dir, 'growth_trends.md')
    with open(out_path, 'w') as f:
        f.write(content.strip() + "\n")
    print(f"Growth Trends Report written to {out_path}")

if __name__ == '__main__':
    main()
