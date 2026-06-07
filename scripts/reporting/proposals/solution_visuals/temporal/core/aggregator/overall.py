import os
import yaml
import pandas as pd
from ..loader import discover_csv_files, parse_date_column
from utils.column_finder import locate_column

def aggregate_overall(base_dir: str, config: dict) -> dict:
    """Aggregate total registrations per year-month.
    Returns a dict mapping (year, month) -> count.
    """
    csv_files = discover_csv_files(base_dir, config['data']['files_pattern'])
    monthly_counts = {}
    for f in csv_files:
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        if '2017' in os.path.basename(f):
            col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[col])
            counts = df[col].dropna().value_counts()
            for month, cnt in counts.items():
                try:
                    m = int(float(month))
                    if 1 <= m <= 12:
                        monthly_counts[(2017, m)] = monthly_counts.get((2017, m), 0) + cnt
                except ValueError:
                    pass
            continue
        date_col = locate_column(cols, ['FECHA PROCESO', 'FECHA COMPRA'])
        if not date_col:
            continue
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col])
        df = df.dropna(subset=[date_col])
        df = parse_date_column(df, date_col)
        df = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]
        counts = df.groupby(['year', 'month']).size()
        for (y, m), cnt in counts.items():
            monthly_counts[(int(y), int(m))] = monthly_counts.get((int(y), int(m)), 0) + cnt
    return monthly_counts
