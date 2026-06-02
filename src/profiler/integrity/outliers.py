import pandas as pd
import numpy as np
from typing import Dict, Any

def detect_iqr_outliers(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """
    Identifies outliers in a numeric column using the Interquartile Range (IQR) method.
    """
    series = df[col].dropna()
    if series.empty:
        return {"outliers_count": 0, "outliers_percentage": 0.0}
        
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = series[(series < lower_bound) | (series > upper_bound)]
    outliers_count = len(outliers)
    total_count = len(df[col])
    
    return {
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "outliers_count": int(outliers_count),
        "outliers_percentage": round((outliers_count / total_count) * 100, 4) if total_count > 0 else 0.0,
        "sample_outliers": [float(x) for x in outliers.head(10).tolist()]
    }

def profile_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Profiles outliers across all numeric columns using IQR.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    outlier_profiles = {}
    
    for col in numeric_cols:
        outlier_profiles[col] = detect_iqr_outliers(df, col)
        
    return outlier_profiles
