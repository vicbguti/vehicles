import os
import sys
import json
import yaml
from glob import glob

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    
    with open(os.path.join(cache_dir, 'evolution.json'), 'r') as f:
        evolution = json.load(f)
        
    annual_dirs = sorted(glob(os.path.join(cache_dir, 'annual/*')))
    annual = {}
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
        year = os.path.basename(dir_path)
        
        # Load uniqueness
        with open(os.path.join(dir_path, 'uniqueness.json'), 'r') as f:
            uniqueness = json.load(f)
        # Load completeness
        with open(os.path.join(dir_path, 'completeness.json'), 'r') as f:
            completeness = json.load(f)
            
        annual[year] = {
            "row_count": uniqueness['total_records'],
            "uniqueness": uniqueness,
            "completeness": completeness
        }
            
    years = sorted(list(annual.keys()))
    
    # Analyze null rates for a sample year (e.g. 2025)
    sample_year = "2025" if "2025" in annual else years[-1]
    completeness_data = annual[sample_year]['completeness']['metrics']
    null_table = "| Column | Null Count | Null % | Status |\n|---|---|---|---|\n"
    for col, metrics in sorted(completeness_data.items(), key=lambda x: x[1]['null_percentage'], reverse=True):
        status = "CRITICAL" if metrics['null_percentage'] > 50 else ("WARNING" if metrics['null_percentage'] > 5 else "OK")
        null_table += f"| {col} | {metrics['null_count']:,} | {metrics['null_percentage']:.2f}% | {status} |\n"

    # Analyze duplicates
    duplicates_table = "| Year | Row Count | Duplicate Rows | Duplicate % |\n|---|---|---|---|\n"
    for year in years:
        row_count = annual[year]['row_count']
        dup_count = annual[year]['uniqueness']['duplicate_rows_count']
        dup_pct = annual[year]['uniqueness']['duplicate_rows_percentage']
        duplicates_table += f"| {year} | {row_count:,} | {dup_count:,} | {dup_pct:.2f}% |\n"

    content = f"""# Data Quality and Integrity Audit Report

This report assesses schema evolution, data completeness (missingness), row duplication, and business rules anomalies.

## 1. Schema Evolution & Consistency
* **Drift Status**: { "Drift Detected" if evolution['drift_detected'] else "Clean / Uniform" }
* **Common Columns**: {len(evolution['common_columns_all_periods'])} columns are present in every annual file.
* **Summary of Changes**: Columns names and logical layouts are highly consistent across the years, indicating that data structure is ready for integrated temporal modeling.

## 2. Completeness Profile ({sample_year} Example)
Specific columns exhibit high null rates, which requires imputation or exclusion policies.

{null_table}

## 3. Duplication Rates
The dataset contains duplicate records that must be resolved (e.g., exact matches).

{duplicates_table}
"""
    out_path = os.path.join(paths['reports_dir'], '01_quality_audit.md')
    with open(out_path, 'w') as f:
        f.write(content.strip() + "\n")
    print(f"Data Quality Audit Report written to {out_path}")

if __name__ == '__main__':
    main()
