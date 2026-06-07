import os
import pandas as pd
from ..excel_dictionary import read_canton_sheet

# ----------------------------------------------------------------------
# Global caches (populated once at import time)
# ----------------------------------------------------------------------
_CANTON_MAP: dict[str, str] = {}
_CANTON_TO_PROV_MAP: dict[str, str] = {}


def _load_maps() -> None:
    """Populate the lookup dictionaries from the canton data sheet.

    This runs once when the module is imported, ensuring fast look‑ups.
    """
    df = read_canton_sheet()
    for _, row in df.iterrows():
        # Normalise identifiers – sheet may contain numbers or strings
        canton_code = str(int(float(row["canton_code"]))).strip()
        canton_name = str(row["canton_desc"]).strip()
        province_name = str(row["province_desc"]).strip()
        if canton_code:
            _CANTON_MAP[canton_code] = canton_name
            _CANTON_TO_PROV_MAP[canton_code] = province_name

# Load caches at import time
_load_maps()


def code_to_name(canton_code: str) -> str | None:
    """Return the human‑readable canton name for a given canton code.

    Returns ``None`` if the code is not present in the dictionary.
    """
    return _CANTON_MAP.get(str(canton_code).strip())


def code_to_province(canton_code: str) -> str | None:
    """Return the province name that the canton belongs to.

    The original code base expected a ``code_to_province`` function that
    accepted a *canton* code, so we keep the name for backward compatibility.
    """
    return _CANTON_TO_PROV_MAP.get(str(canton_code).strip())

# Optional explicit alias if other code expects a different name
canton_code_to_province = code_to_province
