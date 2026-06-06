import os
import yaml
import pandas as pd

def read_canton_sheet():
    """Read the "Catálogo_Cantones" sheet from the data dictionary.
    Returns a pandas DataFrame with columns:
        canton_code, canton_desc, province_code, province_desc
    """
    # Re‑use the shared config loader for paths
    from .config_loader import load_config
    cfg, project_root = load_config()
    dict_path = os.path.join(project_root, cfg['data']['dictionary'])
    if not os.path.exists(dict_path):
        # fallback to legacy relative location
        dict_path = os.path.join(os.path.dirname(__file__), '../../../../../', cfg['data']['dictionary'])
    df = pd.read_excel(dict_path, sheet_name='Catálogo_Cantones', skiprows=1)
    df.columns = ['canton_code', 'canton_desc', 'province_code', 'province_desc']
    return df
