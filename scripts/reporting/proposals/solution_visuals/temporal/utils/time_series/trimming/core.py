import pandas as pd
from typing import Iterable

from utils.time_series.trimming.config import DEFAULT_EXCLUDE


def trim_zero_tail(
    df: pd.DataFrame,
    date_col: str,
    exclude_cols: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Trim trailing rows where all metric columns are zero.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    date_col : str
        Column name that holds the datetime values (used for sorting).
    exclude_cols : iterable of str, optional
        Columns that should be ignored when determining metric columns.
        By default ``year`` and ``month`` are excluded via ``DEFAULT_EXCLUDE``.
    """
    if exclude_cols is None:
        exclude_cols = DEFAULT_EXCLUDE
    # Ensure the date column is sorted
    df = df.sort_values(by=date_col)
    # Metric columns = all columns except the date column and any exclusions
    metric_cols = df.columns.difference([date_col] + list(exclude_cols))
    if metric_cols.empty:
        return df
    # Identify rows that have any non-zero metric value
    non_zero_mask = (df[metric_cols] != 0).any(axis=1)
    if not non_zero_mask.any():
        # All rows are zero – return empty DataFrame
        return df.iloc[0:0]
    last_valid_idx = non_zero_mask[non_zero_mask].index[-1]
    return df.loc[:last_valid_idx]
