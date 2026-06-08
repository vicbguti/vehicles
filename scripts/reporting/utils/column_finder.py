import unicodedata

def _normalize(s: str) -> str:
    """Strip accents, spaces, underscores and convert to upper‑case.
    Handles Spanish accented characters such as "CANTÓN".
    """
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s.replace(' ', '').replace('_', '').upper()
def locate_column(columns: list[str], candidates: list[str], fallback_to_canton: bool = False) -> str | None:
    """Return the first column matching any of *candidates*.
    * Normalises both column names and candidates.
    * If *fallback_to_canton* is True and no match is found, returns the first column
      containing the token "CANTON" after normalisation.
    """
    norm_candidates = [_normalize(c) for c in candidates]
    for col in columns:
        col_norm = _normalize(col)
        for cand in norm_candidates:
            if cand in col_norm:
                return col
    if fallback_to_canton:
        for col in columns:
            if 'CANTON' in _normalize(col):
                return col
    return None


# Backwards‑compatible wrapper – older code used ``find_column``
def find_column(columns, candidates, exact=False):
    """Legacy API retained for compatibility.
    If *exact* is True, perform an exact upper‑case match; otherwise behave like
    ``locate_column`` without the canton fallback.
    """
    if exact:
        for opt in candidates:
            for c in columns:
                if c.strip().upper() == opt.upper():
                    return c
    else:
        return locate_column(columns, candidates)
