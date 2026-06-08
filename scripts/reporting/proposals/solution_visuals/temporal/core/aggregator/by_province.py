import os
import yaml
import pandas as pd
from ..loader import discover_csv_files, parse_date_column
from utils.column_finder import locate_column
from utils.geo_mapper.mapper import code_to_province

def aggregate_by_province(base_dir: str, config: dict, target_provinces=None) -> dict:
    """Aggregate registrations per province per year-month.
    Returns a dict mapping (year, month, province) -> count.
    """
    if target_provinces is None:
        target_provinces = []
    csv_files = discover_csv_files(base_dir, config['data']['files_pattern'])
    monthly_counts = {}
    for f in csv_files:
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        province_col = locate_column(cols, ['CANTON', 'CANTON CODIGO', 'CANTON COD', 'CANTÓN'])
        if not province_col:
            continue
        if '2017' in os.path.basename(f):
            date_col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, province_col])
            df = df.dropna(subset=[date_col, province_col])
            counts = df.groupby([date_col, province_col]).size()
            for (month, prov), cnt in counts.items():
                try:
                    m = int(float(month))
                    if 1 <= m <= 12:
                        try:
                            c_str = str(int(float(prov))).strip()
                            prov_name = code_to_province(c_str)
                        except (ValueError, TypeError):
                            prov_name = None
                        if prov_name:
                            prov_up = prov_name.upper()
                            if not target_provinces or prov_up in target_provinces:
                                key = (2017, m, prov_up)
                                monthly_counts[key] = monthly_counts.get(key, 0) + cnt
                except ValueError:
                    pass
            continue
        date_col = locate_column(cols, ['FECHA PROCESO', 'FECHA COMPRA'])
        if not date_col:
            continue
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, province_col])
        df = df.dropna(subset=[date_col, province_col])
        df = parse_date_column(df, date_col)
        df = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]
        counts = df.groupby(['year', 'month', province_col]).size()
        for (y, m, prov), cnt in counts.items():
            try:
                c_str = str(int(float(prov))).strip()
                prov_name = code_to_province(c_str)
            except (ValueError, TypeError):
                prov_name = None
            if prov_name:
                prov_up = prov_name.upper()
                if not target_provinces or prov_up in target_provinces:
                    key = (int(y), int(m), prov_up)
                    monthly_counts[key] = monthly_counts.get(key, 0) + cnt
    return monthly_counts

