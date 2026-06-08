import os
import sys
import yaml
import json
from glob import glob

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.profiler.structure.evolution import compare_schemas
from src.profiler.temporal.yoy_growth import calculate_yoy_growth

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    annual_cache_dir = os.path.join(cache_dir, 'annual')
    
    annual_dirs = sorted(glob(os.path.join(annual_cache_dir, '*')))
    if not annual_dirs:
        print("No annual cache directories found. Run annual profiling first.")
        sys.exit(1)
        
    schemas = {}
    annual_counts = {}
    
    print("Loading annual chunked caches for cross-period analysis...")
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
            
        year_str = os.path.basename(dir_path)
        
        # Load record_count
        count_path = os.path.join(dir_path, 'record_count.json')
        with open(count_path, 'r') as f:
            count_data = json.load(f)
        annual_counts[year_str] = count_data['row_count']
        
        # Load types
        types_path = os.path.join(dir_path, 'types.json')
        with open(types_path, 'r') as f:
            types_data = json.load(f)
        schemas[year_str] = {col: info['physical_type'] for col, info in types_data.items()}
        
    print("Running cross-year schema comparison...")
    evolution = compare_schemas(schemas)
    
    print("Calculating YoY growth rates...")
    growth = calculate_yoy_growth(annual_counts)
    
    with open(os.path.join(cache_dir, 'evolution.json'), 'w') as f:
        json.dump(evolution, f, indent=2, default=str)
        
    with open(os.path.join(cache_dir, 'growth.json'), 'w') as f:
        json.dump(growth, f, indent=2, default=str)
        
    print("Cross-period profiling completed.")

if __name__ == '__main__':
    main()
