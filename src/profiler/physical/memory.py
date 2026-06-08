import pandas as pd
import os
from typing import Dict, Any

def profile_dataframe_memory(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Profiles the memory usage of a pandas DataFrame.
    Returns a dictionary containing shallow memory, deep memory,
    per-column memory usage, and optimization suggestions.
    """
    # Shallow memory (ignores actual strings size in object columns)
    shallow_bytes = df.memory_usage().sum()
    
    # Deep memory (profiles actual object contents like string lengths)
    deep_bytes = df.memory_usage(deep=True).sum()
    
    column_memory = df.memory_usage(deep=True).to_dict()
    # Remove index memory from per-column breakdown if present
    column_memory.pop('Index', None)
    
    # Calculate potential optimization by converting 'object' type columns to 'category'
    potential_savings_bytes = 0
    suggestions = {}
    
    for col in df.columns:
        if df[col].dtype == 'object':
            num_unique = df[col].nunique()
            total_vals = len(df[col])
            
            # Simple heuristic: if unique values are < 50% of total rows, category might save memory
            if total_vals > 0 and (num_unique / total_vals) < 0.5:
                # Calculate what the memory would be if converted to category
                cat_col = df[col].astype('category')
                cat_bytes = cat_col.memory_usage(deep=True)
                current_bytes = column_memory.get(col, 0)
                
                savings = current_bytes - cat_bytes
                if savings > 0:
                    potential_savings_bytes += savings
                    suggestions[col] = {
                        "current_bytes": current_bytes,
                        "optimized_bytes": cat_bytes,
                        "savings_bytes": savings,
                        "unique_count": num_unique,
                        "suggestion": "Convert to category"
                    }
                    
    return {
        "shallow_bytes": int(shallow_bytes),
        "deep_bytes": int(deep_bytes),
        "columns": {col: int(bytes_val) for col, bytes_val in column_memory.items()},
        "potential_savings_bytes": int(potential_savings_bytes),
        "optimized_deep_bytes": int(deep_bytes - potential_savings_bytes),
        "suggestions": suggestions
    }
