import pandas as pd
from typing import Dict, Any, List

def profile_business_anomalies(df: pd.DataFrame, rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Profiles rows violating logic constraints (rules).
    Example rules:
    {
      "value_bounds": {
         "anio_modelo": {"min": 1900, "max": 2027}
      },
      "logical_constraints": [
         {"name": "registration_date_after_model_year", "expression": "registration_year >= anio_modelo"}
      ]
    }
    """
    anomalies_report = {}
    total_records = len(df)
    
    # 1. Check Value Boundaries
    bounds_violations = {}
    if "value_bounds" in rules:
        for col, bound in rules["value_bounds"].items():
            if col not in df.columns:
                continue
            
            series = df[col].dropna()
            if series.empty:
                continue
                
            # Coerce to numeric for bounds checking
            series_numeric = pd.to_numeric(series, errors='coerce')
            
            col_violations = 0
            if "min" in bound:
                col_violations += int((series_numeric < bound["min"]).sum())
            if "max" in bound:
                col_violations += int((series_numeric > bound["max"]).sum())
                
            if col_violations > 0:
                bounds_violations[col] = {
                    "violations_count": col_violations,
                    "violations_percentage": round((col_violations / total_records) * 100, 4) if total_records > 0 else 0.0
                }
                
    # 2. Check Logical Constraints
    constraint_violations = {}
    if "logical_constraints" in rules:
        for constraint in rules["logical_constraints"]:
            name = constraint["name"]
            expr = constraint["expression"]
            
            try:
                # Query df using the expression
                violators = df.query(f"not ({expr})")
                violations_count = len(violators)
                
                if violations_count > 0:
                    constraint_violations[name] = {
                        "expression": expr,
                        "violations_count": violations_count,
                        "violations_percentage": round((violations_count / total_records) * 100, 4) if total_records > 0 else 0.0
                    }
            except Exception as e:
                constraint_violations[name] = {
                    "expression": expr,
                    "error": str(e)
                }
                
    return {
        "value_bounds_violations": bounds_violations,
        "logical_constraint_violations": constraint_violations
    }
