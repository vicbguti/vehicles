import os
import glob
import pandas as pd
from datetime import datetime

def parse_date_series(series: pd.Series, fmt: str = "%d/%m/%Y") -> pd.Series:
    """Convert a string series (e.g. '28/2/2026') to pandas Timestamps.
    Empty or malformed entries become NaT.
    """
    return pd.to_datetime(series.str.strip(), format=fmt, errors="coerce")

def get_latest_date(csv_pattern: str, date_column_name: str) -> datetime | None:
    """Return the maximum date found in *date_column_name* across all CSV files matching *csv_pattern*.
    The function reads only the required column to keep memory usage low.
    Returns ``None`` if no valid dates are present.
    """
    max_date = None
    for f in sorted(glob.glob(csv_pattern)):
        try:
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_column_name])
        except ValueError:
            # Column not present in this file – skip
            continue
        dates = parse_date_series(df[date_column_name])
        cur_max = dates.max()
        if pd.notnull(cur_max) and (max_date is None or cur_max > max_date):
            max_date = cur_max
    return max_date
