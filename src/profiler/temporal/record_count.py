import pandas as pd
from typing import Dict, Any

def get_record_count(df: pd.DataFrame) -> int:
    """
    Returns the logical row count for a given DataFrame.
    """
    return len(df)

def profile_temporal_record_counts(dfs: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """
    Given a dict of period_label -> DataFrame, returns counts for each period.
    """
    return {label: get_record_count(df) for label, df in dfs.items()}
