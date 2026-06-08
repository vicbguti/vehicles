import pandas as pd
from typing import Dict, Any

def profile_completeness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes missing data (completeness) rates across all columns.
    """
    total_records = len(df)
    completeness_metrics = {}
    
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        non_null_count = total_records - null_count
        null_percentage = round((null_count / total_records) * 100, 4) if total_records > 0 else 0.0
        
        completeness_metrics[col] = {
            "null_count": null_count,
            "non_null_count": non_null_count,
            "null_percentage": null_percentage,
            "completeness_percentage": round(100.0 - null_percentage, 4),
            "is_fully_populated": null_count == 0
        }
        
    return {
        "total_records": total_records,
        "metrics": completeness_metrics
    }
