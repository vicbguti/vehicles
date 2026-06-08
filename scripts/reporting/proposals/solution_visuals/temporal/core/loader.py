import os
import sys
import yaml
import pandas as pd
from glob import glob

from utils.date import parse_date, parse_slash_date

def discover_csv_files(base_dir: str, pattern: str) -> list:
    """Return a sorted list of CSV file paths matching the given pattern.
    The pattern is relative to the project root (e.g., 'data/*.csv').
    """
    search_path = os.path.abspath(os.path.join(base_dir, pattern))
    files = sorted(glob(search_path))
    return files

# NOTE: The legacy ``match_column`` function has been removed. Use ``utils.column_finder.locate_column`` instead.


def parse_date_column(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Parse the *date_col* values into separate *year* and *month* columns.
    Handles slash dates (MM/DD vs DD/MM) and Spanish textual dates.
    """
    is_mm_dd = "MM/DD" in date_col
    dates = df[date_col].astype(str)
    parsed = dates.apply(lambda v: parse_slash_date(v, is_mm_dd) if '/' in v else parse_date(v))
    df['year'] = parsed.apply(lambda t: t[0])
    df['month'] = parsed.apply(lambda t: t[1])
    return df
