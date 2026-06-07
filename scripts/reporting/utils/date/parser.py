from ..constants import SPANISH_MONTHS


def parse_date(val):
    """
    Parse a raw date string from the SRI CSV files into (year, month) integers.

    Supported formats:
        - "MM/DD/YYYY"   → slash, MM first (column name contains 'MM/DD')
        - "DD/MM/YYYY"   → slash, DD first (default slash path)
        - "DD-MON-YYYY"  → Spanish three-letter month abbreviation (2020-2023) (or 2‑digit year e.g., 27-Nov-20)
        - "YYYY 21:50"   → year‑only with time suffix (2017 special handling)

    Returns:
        (year: int, month: int) or (0, 0) on parse failure.
    """
    s = str(val).strip()
    if not s or s == 'nan':
        return 0, 0

    # Spanish dash format: DD-ENE-2021 (or 2‑digit year e.g., 27-Nov-20)
    if '-' in s and not s.replace('-', '').isdigit():
        parts = s.split('-')
        if len(parts) == 3:
            mon_str = parts[1].strip().upper()
            month = SPANISH_MONTHS.get(mon_str, 0)
            if month:
                try:
                    year_str = parts[2].strip().split()[0]
                    year = int(year_str)
                    if year < 100:
                        year += 2000
                    return year, month
                except (ValueError, IndexError):
                    pass
        return 0, 0

    # Slash format: MM/DD/YYYY or DD/MM/YYYY
    if '/' in s:
        parts = s.split('/')
        if len(parts) == 3:
            return _parse_slash(parts)
        return 0, 0

    # Fallback: plain year (e.g., "2018" or "2018 21:50")
    try:
        year = int(s.split()[0])
        return year, 0
    except (ValueError, IndexError):
        return 0, 0


def parse_slash_date(val, is_mm_dd=False):
    """
    Parse a slash‑separated date string.

    Args:
        val: raw cell value.
        is_mm_dd: True if the column header signals MM/DD/YYYY ordering.

    Returns:
        (year: int, month: int) or (0, 0) on failure.
    """
    s = str(val).strip()
    parts = s.split('/')
    if len(parts) != 3:
        return 0, 0
    return _parse_slash(parts, is_mm_dd=is_mm_dd)


def _parse_slash(parts, is_mm_dd=False):
    try:
        if is_mm_dd:
            month = int(parts[0].strip())
        else:
            month = int(parts[1].strip())
        year_str = parts[2].strip().split()[0]
        if len(year_str) == 2:
            year = 2000 + int(year_str)
        else:
            year = int(year_str)
        return year, month
    except (ValueError, IndexError):
        return 0, 0
