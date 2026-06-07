import os
import yaml
import pandas as pd
from ..loader import discover_csv_files, parse_date_column
from utils.column_finder import locate_column

from utils.geo_mapper.mapper import code_to_province

def aggregate_combined(base_dir: str, config: dict, target_classes=None, target_provinces=None) -> dict:
    """Aggregate registrations per province and class per year-month.
    Returns a dict mapping (year, month, province, class) -> count.
    """
    if target_classes is None:
        target_classes = ['MOTOCICLETA', 'JEEP', 'AUTOMOVIL', 'CAMIONETA', 'CAMON']
    csv_files = discover_csv_files(base_dir, config['data']['files_pattern'])
    monthly_counts = {}
    for f in csv_files:
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()
        class_col = locate_column(cols, ['CLASE', 'Clase'])
        prov_col = locate_column(cols, ['CANTON', 'CANTON CODIGO', 'CANTON COD'], fallback_to_canton=True)
        if not class_col or not prov_col:
            continue
        if '2017' in os.path.basename(f):
            date_col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, class_col, prov_col])
            df = df.dropna(subset=[date_col, class_col, prov_col])
            counts = df.groupby([date_col, class_col, prov_col]).size()
            for (month, cl, prov), cnt in counts.items():
                try:
                    m = int(float(month))
                    cl_up = str(cl).strip().upper()
                    if 1 <= m <= 12 and cl_up in target_classes:
                        try:
                            c_str = str(int(float(prov))).strip()
                            prov_name = code_to_province(c_str)
                        except (ValueError, TypeError):
                            prov_name = None
                        if prov_name:
                            prov_up = prov_name.upper()
                            key = (2017, m, prov_up, cl_up)
                            monthly_counts[key] = monthly_counts.get(key, 0) + cnt
                except ValueError:
                    pass
            continue
        date_col = locate_column(cols, ['FECHA PROCESO', 'FECHA COMPRA'])
        if not date_col:
            continue
        df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col, class_col, prov_col])
        df = df.dropna(subset=[date_col, class_col, prov_col])
        df = parse_date_column(df, date_col)
        df = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]
        counts = df.groupby(['year', 'month', class_col, prov_col]).size()
        for (y, m, cl, prov), cnt in counts.items():
            cl_up = str(cl).strip().upper()
            try:
                c_str = str(int(float(prov))).strip()
                prov_name = code_to_province(c_str)
            except (ValueError, TypeError):
                prov_name = None
            if prov_name and cl_up in target_classes:
                prov_up = prov_name.upper()
                key = (int(y), int(m), prov_up, cl_up)
                monthly_counts[key] = monthly_counts.get(key, 0) + cnt
    return monthly_counts
