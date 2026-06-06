def find_column(columns, candidates, exact=False):
    """Return the first column name that matches any of the candidate strings.

    Parameters
    ----------
    columns : list[str]
        List of column names from the CSV header.
    candidates : list[str]
        Possible substrings (case‑insensitive) for the desired column.
    exact : bool, optional
        If True, require exact equality (c.strip().upper() == opt.upper()).
        If False (default), match if the candidate appears anywhere in the column name.

    Returns
    -------
    str | None
        The matching column name, or None if no match is found.
    """
    for opt in candidates:
        for c in columns:
            if exact:
                if c.strip().upper() == opt.upper():
                    return c
            else:
                if opt.upper() in c.strip().upper():
                    return c
    return None
