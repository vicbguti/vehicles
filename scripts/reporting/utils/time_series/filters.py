import pandas as pd

def trim_trailing_metric(
    df: pd.DataFrame,
    metric_col: str,
    date_col: str,
) -> pd.DataFrame:
    """Remove trailing rows where the selected ``metric_col`` is zero.

    The DataFrame is first sorted by ``date_col`` to guarantee chronological
    order. Then the function finds the last row where ``metric_col`` is non‑zero
    and returns the slice up to (and including) that row. If *all* rows have a
    zero value for ``metric_col`` an empty DataFrame is returned.

    Parameters
    ----------
    df : pandas.DataFrame
        Data containing at least ``date_col`` and ``metric_col``.
    metric_col : str
        Name of the column whose zero values should trigger the trim.
    date_col : str
        Name of the column used for chronological ordering (e.g. "date_label").

    Returns
    -------
    pandas.DataFrame
        ``df`` with trailing zero‑metric rows removed.
    """
    import pandas as pd

    # Ensure chronological ordering
    df = df.sort_values(by=date_col)

    # Identify rows where the metric column is non‑zero
    non_zero_mask = df[metric_col] != 0
    if not non_zero_mask.any():
        # All rows are zero → return empty DataFrame
        return df.iloc[0:0]

    # Locate the last index with a non‑zero metric value
    last_valid_idx = non_zero_mask[non_zero_mask].index[-1]
    return df.loc[:last_valid_idx]
