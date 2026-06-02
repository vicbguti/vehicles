import os
import sys
import yaml
import json
import time
from glob import glob
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.profiler.physical.memory import profile_dataframe_memory
from src.profiler.structure.types import profile_column_types
from src.profiler.structure.cardinality import profile_column_cardinality
from src.profiler.integrity.completeness import profile_completeness
from src.profiler.integrity.statistics import profile_descriptive_statistics
from src.profiler.integrity.outliers import profile_outliers
from src.profiler.integrity.uniqueness import profile_uniqueness
from src.profiler.integrity.anomalies import profile_business_anomalies
from src.profiler.temporal.record_count import get_record_count
from src.profiler.temporal.seasonality import profile_seasonality

def save_metric(dir_path, filename, data):
    with open(os.path.join(dir_path, filename), 'w') as f:
        json.dump(data, f, indent=2, default=str)

def profile_single_file(file_path: str, reports_dir: str):
    file_name = os.path.basename(file_path)
    year_str = "".join([c for c in file_name if c.isdigit()])
    if not year_str:
        year_str = file_name
        
    print(f"Processing: {file_name}...")
    start_time = time.time()
    
    # Load CSV (semi-colon separated, latin1 encoded)
    df = pd.read_csv(file_path, sep=';', encoding='latin1')
    load_time = time.time() - start_time
    
    year_dir = os.path.join(reports_dir, 'cache/annual', year_str)
    os.makedirs(year_dir, exist_ok=True)
    
    # Basic logical metrics & record count
    row_count = get_record_count(df)
    save_metric(year_dir, "record_count.json", {"row_count": row_count, "load_time_seconds": round(load_time, 2)})
    
    # Memory metrics
    mem_profile = profile_dataframe_memory(df)
    save_metric(year_dir, "memory.json", mem_profile)
    
    # Structure metrics
    col_types = profile_column_types(df)
    save_metric(year_dir, "types.json", col_types)
    
    # Determine categorical columns for cardinality (object columns)
    cat_cols = [col for col, info in col_types.items() if info['logical_type'] == 'categorical' or df[col].dtype == 'object']
    cardinality_profile = profile_column_cardinality(df, cat_cols)
    save_metric(year_dir, "cardinality.json", cardinality_profile)
    
    # Integrity metrics
    completeness = profile_completeness(df)
    save_metric(year_dir, "completeness.json", completeness)
    
    desc_stats = profile_descriptive_statistics(df)
    save_metric(year_dir, "statistics.json", desc_stats)
    
    outliers = profile_outliers(df)
    save_metric(year_dir, "outliers.json", outliers)
    
    uniqueness = profile_uniqueness(df, potential_keys=['Código Vehículo 1'])
    save_metric(year_dir, "uniqueness.json", uniqueness)
    
    rules = {
        "value_bounds": {
            "Año Modelo": {"min": 1900, "max": 2027},
            "Cilindraje": {"min": 0, "max": 20000},
            "Valor Avaluo": {"min": 0, "max": 5000000}
        },
        "logical_constraints": [
            {
                "name": "registration_date_after_model_year", 
                "expression": "`Año Modelo` <= 2027"
            }
        ]
    }
    anomalies = profile_business_anomalies(df, rules)
    save_metric(year_dir, "anomalies.json", anomalies)
    
    # Seasonality
    seasonality = {}
    if 'Mes Adquisición' in df.columns:
        df_temp = df.copy()
        df_temp['date_dummy'] = pd.to_datetime('2020-' + df_temp['Mes Adquisición'].astype(str).str.zfill(2) + '-01', format='%Y-%m-%d', errors='coerce')
        seasonality = profile_seasonality(df_temp, 'date_dummy')
    save_metric(year_dir, "seasonality.json", seasonality)
        
    print(f"Finished {file_name} in {load_time:.2f}s. Saved chunked metrics to {year_dir}")

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    data_cfg = config['data']
    
    annual_files = sorted(glob(data_cfg['files_pattern']))
    if not annual_files:
        print("No raw files found.")
        sys.exit(1)
        
    for file_path in annual_files:
        profile_single_file(file_path, paths['reports_dir'])

if __name__ == '__main__':
    main()
