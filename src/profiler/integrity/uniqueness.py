import pandas as pd
from typing import Dict, Any, List

def profile_uniqueness(df: pd.DataFrame, potential_keys: List[str] = None) -> Dict[str, Any]:
    """
    Analyzes row duplicates and duplicate rates of potential unique identifiers.
    """
    total_records = len(df)
    
    # 1. Total row deduplication
    duplicate_rows_count = int(df.duplicated().sum())
    duplicate_rows_percentage = round((duplicate_rows_count / total_records) * 100, 4) if total_records > 0 else 0.0
    
    # 2. Key uniqueness checks
    key_metrics = {}
    if potential_keys:
        for key in potential_keys:
            if key not in df.columns:
                continue
                
            unique_keys = df[key].nunique(dropna=True)
            null_keys = int(df[key].isnull().sum())
            non_null_keys = total_records - null_keys
            
            is_unique = (unique_keys == non_null_keys) and (null_keys == 0)
            duplicate_keys_count = int(df.duplicated(subset=[key]).sum()) - null_keys
            
            key_metrics[key] = {
                "unique_values": unique_keys,
                "null_values": null_keys,
                "is_unique_identifier": is_unique,
                "duplicate_keys_count": max(0, duplicate_keys_count),
                "duplication_rate": round((duplicate_keys_count / total_records) * 100, 4) if total_records > 0 else 0.0
            }
            
    return {
        "total_records": total_records,
        "duplicate_rows_count": duplicate_rows_count,
        "duplicate_rows_percentage": duplicate_rows_percentage,
        "key_uniqueness_metrics": key_metrics
    }
