import os
import yaml
import pandas as pd
from ..loader import discover_csv_files
from utils.date import parse_date, parse_slash_date
from utils.geo_mapper.mapper import code_to_province
from utils.column_finder import locate_column



def aggregate_by_canton(base_dir: str, config: dict, target_cantons: list | None = None) -> dict:
    """Aggregate registrations per canton, class, sub‑class and type per year‑month.

    Returns a dict mapping (year, month, canton, class, sub_class, type) -> count.
    Missing sub‑class or type columns are filled with the placeholder "UNKNOWN".
    """
    if target_cantons is None:
        target_cantons = []  # empty list means no filtering
    csv_files = discover_csv_files(base_dir, config['data']['files_pattern'])
    monthly_counts = {}
    for f in csv_files:
        # Load a tiny sample to discover column names
        df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1)
        cols = df_head.columns.tolist()

        # Identify relevant columns
        canton_col = locate_column(cols, ['CANTON', 'CANTON CODIGO', 'CANTON COD', 'CANTÓN'])
        class_col = locate_column(cols, ['CLASE', 'Clase'])
        sub_class_col = locate_column(cols, ['SUB CLASE', 'Sub Clase', 'SUBCLASE'])
        type_col = locate_column(cols, ['TIPO', 'Tipo', 'TYPE'])
        if not canton_col or not class_col:
            # Without canton or class we cannot aggregate meaningfully
            continue

        # Resolve missing sub‑class / type columns
        sub_class_col = sub_class_col if sub_class_col else None
        type_col = type_col if type_col else None

        # Determine which columns to read for efficiency
        usecols = [canton_col, class_col]
        if sub_class_col:
            usecols.append(sub_class_col)
        if type_col:
            usecols.append(type_col)

        # Special handling for 2017 files (different date column name)
        if '2017' in os.path.basename(f):
            date_col = 'Mes Adquisición' if 'Mes Adquisición' in cols else 'Mes  registro venta'
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col] + usecols)
            df = df.dropna(subset=[date_col] + usecols)
            # No year info in 2017 files, assume year 2017
            df['year'] = 2017
            df['month'] = df[date_col].apply(lambda v: int(float(v)) if str(v).replace('.','',1).isdigit() else None)
            df = df[(df['month'] >= 1) & (df['month'] <= 12)]
        else:
            # Regular files: discover date column dynamically
            date_col = None
            for opt in ['FECHA PROCESO', 'FECHA COMPRA']:
                for c in cols:
                    if opt.upper() in c.strip().upper():
                        date_col = c
                        break
                if date_col:
                    break
            if not date_col:
                continue
            df = pd.read_csv(f, sep=';', encoding='latin1', usecols=[date_col] + usecols)
            df = df.dropna(subset=[date_col] + usecols)
            # Parse dates (handles slash dates and spanish textual dates)
            is_mm_dd = 'MM/DD' in date_col
            dates = df[date_col].astype(str)
            parsed = dates.apply(lambda v: parse_slash_date(v, is_mm_dd) if '/' in v else parse_date(v))
            df['year'] = parsed.apply(lambda t: t[0])
            df['month'] = parsed.apply(lambda t: t[1])
            df = df[(df['month'] >= 1) & (df['month'] <= 12) & (df['year'] >= 2017) & (df['year'] <= 2026)]

        # Normalise canton code (strip leading zeros, ensure string)
        df['canton_str'] = df[canton_col].apply(lambda x: str(int(float(x))).strip() if pd.notnull(x) else "")
        # Optionally filter by target cantons (using raw code)
        if target_cantons:
            df = df[df['canton_str'].isin(target_cantons)]

        # Prepare auxiliary columns with placeholders when missing
        if sub_class_col:
            df['sub_class'] = df[sub_class_col].fillna('UNKNOWN').astype(str).str.strip()
        else:
            df['sub_class'] = 'UNKNOWN'
        if type_col:
            df['type'] = df[type_col].fillna('UNKNOWN').astype(str).str.strip()
        else:
            df['type'] = 'UNKNOWN'

        # Perform aggregation
        grp = df.groupby(['year', 'month', 'canton_str', class_col, 'sub_class', 'type']).size()
        for (y, m, canton, cls, sub, typ), cnt in grp.items():
            key = (int(y), int(m), canton, str(cls).strip().upper(), str(sub).strip().upper(), str(typ).strip().upper())
            monthly_counts[key] = monthly_counts.get(key, 0) + int(cnt)
    return monthly_counts
