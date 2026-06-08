from typing import Dict, Any, List, Set

def compare_schemas(schemas: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    Compares columns and types across different years/files.
    schemas is a dictionary: { "file_or_year_label": { "col_name": "type_name", ... } }
    """
    labels = sorted(list(schemas.keys()))
    if len(labels) < 2:
        return {"drift_detected": False, "message": "At least two schemas are needed to compare evolution."}
        
    evolution_report = {}
    
    # Track union of all columns
    all_columns: Set[str] = set()
    for label in labels:
        all_columns.update(schemas[label].keys())
        
    # Analyze changes from label to label sequentially
    changes: List[Dict[str, Any]] = []
    for i in range(len(labels) - 1):
        prev_label = labels[i]
        curr_label = labels[i+1]
        prev_schema = schemas[prev_label]
        curr_schema = schemas[curr_label]
        
        added = sorted(list(set(curr_schema.keys()) - set(prev_schema.keys())))
        removed = sorted(list(set(prev_schema.keys()) - set(curr_schema.keys())))
        
        # Check type drift on common columns
        type_drift = {}
        common_cols = set(prev_schema.keys()) & set(curr_schema.keys())
        for col in common_cols:
            if prev_schema[col] != curr_schema[col]:
                type_drift[col] = {
                    "from_type": prev_schema[col],
                    "to_type": curr_schema[col]
                }
                
        if added or removed or type_drift:
            changes.append({
                "from_period": prev_label,
                "to_period": curr_label,
                "added_columns": added,
                "removed_columns": removed,
                "type_drift": type_drift
            })
            
    # Find columns present in all periods (intersection)
    intersection_columns = set(schemas[labels[0]].keys())
    for label in labels[1:]:
        intersection_columns.intersection_update(schemas[label].keys())
        
    return {
        "all_observed_columns": sorted(list(all_columns)),
        "common_columns_all_periods": sorted(list(intersection_columns)),
        "evolution_steps": changes,
        "drift_detected": len(changes) > 0
    }
