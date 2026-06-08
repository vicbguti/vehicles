import pandas as pd
from typing import Dict, Any, List

def check_schema_conformity(df: pd.DataFrame, expected_schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Checks if a DataFrame matches the expected column schema.
    expected_schema: Dict of column name to data type string (e.g., 'float64', 'object', 'int64')
    """
    actual_columns = set(df.columns)
    expected_columns = set(expected_schema.keys())
    
    missing_columns = sorted(list(expected_columns - actual_columns))
    unexpected_columns = sorted(list(actual_columns - expected_columns))
    
    type_mismatches = {}
    for col in actual_columns & expected_columns:
        actual_type = str(df[col].dtype)
        expected_type = expected_schema[col]
        # Allow some flexibility, e.g. int vs float if all values check out, but flag strict type mismatch
        if actual_type != expected_type:
            type_mismatches[col] = {
                "expected": expected_type,
                "actual": actual_type
            }
            
    is_conforming = not (missing_columns or type_mismatches)
    
    return {
        "is_conforming": is_conforming,
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "type_mismatches": type_mismatches
    }
