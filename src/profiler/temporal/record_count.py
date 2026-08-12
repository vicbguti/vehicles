import pandas as pd


def get_record_count(df: pd.DataFrame) -> int:
    """
    Returns the logical row count for a given DataFrame.
    """
    return len(df)


def profile_temporal_record_counts(dfs: dict[str, pd.DataFrame]) -> dict[str, int]:
    """
    Given a dict of period_label -> DataFrame, returns counts for each period.
    """
    return {label: get_record_count(df) for label, df in dfs.items()}
