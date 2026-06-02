import pandas as pd
from typing import Dict, Any

def profile_seasonality(df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
    """
    Profiles intra-year registration patterns (seasonality) based on a date column.
    """
    if date_col not in df.columns:
        return {"error": f"Date column '{date_col}' not found in DataFrame."}
        
    # Standardize to datetime
    dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
    if dates.empty:
        return {"error": f"No valid date values found in column '{date_col}'."}
        
    total_dates = len(dates)
    
    # 1. Month representation
    month_counts = dates.dt.month.value_counts().sort_index()
    monthly_profile = {
        int(month): {
            "count": int(count),
            "percentage": round((count / total_dates) * 100, 4)
        }
        for month, count in month_counts.items()
    }
    
    # 2. Day of week representation
    day_counts = dates.dt.dayofweek.value_counts().sort_index()
    day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    weekly_profile = {
        day_names[int(day)]: {
            "count": int(count),
            "percentage": round((count / total_dates) * 100, 4)
        }
        for day, count in day_counts.items()
    }
    
    return {
        "analyzed_records": total_dates,
        "monthly_seasonality": monthly_profile,
        "day_of_week_distribution": weekly_profile
    }
