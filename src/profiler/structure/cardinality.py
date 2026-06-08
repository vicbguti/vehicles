import pandas as pd
from typing import Dict, Any, List

def profile_column_cardinality(df: pd.DataFrame, categorical_cols: List[str], max_top_classes: int = 15) -> Dict[str, Any]:
    """
    Profiles the cardinality and class balance of categorical columns.
    """
    cardinality_report = {}
    
    for col in categorical_cols:
        if col not in df.columns:
            continue
            
        series = df[col]
        total_rows = len(series)
        unique_count = series.nunique(dropna=False)
        null_count = series.isnull().sum()
        
        # Calculate frequency counts
        value_counts = series.value_counts(dropna=False)
        top_classes = []
        
        for val, count in value_counts.head(max_top_classes).items():
            val_str = str(val) if pd.notnull(val) else "NULL/MISSING"
            top_classes.append({
                "value": val_str,
                "count": int(count),
                "percentage": round((count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            })
            
        cardinality_report[col] = {
            "total_records": total_rows,
            "unique_values_count": unique_count,
            "null_count": int(null_count),
            "cardinality_ratio": round(unique_count / total_rows, 5) if total_rows > 0 else 0.0,
            "top_values": top_classes
        }
        
    return cardinality_report
