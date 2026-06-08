import pandas as pd
import numpy as np
from typing import Dict, Any

def profile_descriptive_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes statistical properties for numerical columns in the DataFrame.
    """
    stats_profile = {}
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
            
        stats_profile[col] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "min": float(series.min()),
            "max": float(series.max()),
            "std": float(series.std()) if len(series) > 1 else 0.0,
            "skewness": float(series.skew()) if len(series) > 2 else 0.0,
            "quantiles": {
                "25%": float(series.quantile(0.25)),
                "50%": float(series.quantile(0.50)),
                "75%": float(series.quantile(0.75))
            }
        }
        
    return stats_profile
