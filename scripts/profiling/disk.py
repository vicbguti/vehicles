import os
import sys
import yaml
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.profiler.physical.disk import profile_disk_files

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    data_cfg = config['data']
    
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    print("Profiling disk files...")
    disk_profile = profile_disk_files(data_cfg['files_pattern'])
    
    out_path = os.path.join(cache_dir, 'disk.json')
    with open(out_path, 'w') as f:
        json.dump(disk_profile, f, indent=2, default=str)
        
    print(f"Disk profiling completed. Saved to {out_path}")

if __name__ == '__main__':
    main()
