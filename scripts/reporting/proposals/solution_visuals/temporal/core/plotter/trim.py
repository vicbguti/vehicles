import os
import matplotlib.pyplot as plt
from utils.time_series.trimming import trim_zero_tail, DEFAULT_EXCLUDE


def apply_trim(df, date_col='date_label'):
    """Trim trailing all‑zero rows using the shared helper.
    Returns a new DataFrame.
    """
    # Base trimming
    trimmed = trim_zero_tail(df, date_col=date_col)
    # Optional extra safety: drop any remaining rows where *all* metric columns are zero
    metric_cols = [c for c in trimmed.columns if c not in (date_col, 'year', 'month')]
    if metric_cols:
        trimmed = trimmed[(trimmed[metric_cols] != 0).any(axis=1)]
    return trimmed
