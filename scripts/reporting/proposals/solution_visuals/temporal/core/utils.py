def generate_ticks(df, step=6):
    """Generate tick positions and labels for a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame that contains a ``date_label`` column.
    step : int, optional
        Interval between ticks (default is every 6 entries).

    Returns
    -------
    positions : list[int]
        Index positions for the ticks.
    labels : list[str]
        Corresponding label strings from ``date_label``.
    """
    if 'date_label' not in df.columns:
        raise KeyError('date_label column is required for tick generation')
    positions = list(range(0, len(df), step))
    labels = df['date_label'].iloc[positions].tolist()
    return positions, labels
