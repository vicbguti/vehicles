import pandas as pd
from typing import Dict, Any

def infer_logical_type(series: pd.Series) -> str:
    """
    Infers the logical/semantic data type of a pandas Series.
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        # Check if float or integer
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        return "float"
    
    # For object/string columns
    non_null_values = series.dropna()
    if non_null_values.empty:
        return "empty"
        
    # Check if they look like dates
    try:
        # Check if first few values can be converted to dates
        sample_vals = non_null_values.head(20).astype(str)
        pd.to_datetime(sample_vals, errors='raise')
        return "datetime"
    except (ValueError, TypeError):
        pass
        
    # Check if categorical (low cardinality relative to size)
    unique_count = series.nunique()
    total_count = len(series)
    if total_count > 0 and unique_count < 100 and (unique_count / total_count) < 0.2:
        return "categorical"
        
    return "text"

def profile_column_types(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns physical and inferred logical types for all columns in the DataFrame.
    """
    column_profiles = {}
    for col in df.columns:
        column_profiles[col] = {
            "physical_type": str(df[col].dtype),
            "logical_type": infer_logical_type(df[col])
        }
    return column_profiles
