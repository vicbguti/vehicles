# -*- coding: utf-8 -*-
"""Utility functions for the temporal trends canton‑class workflow.
Provides a simple helper to compute the top‑N cantons by total registration count.
"""
import pandas as pd

def top_n_cantons(df: pd.DataFrame, n: int = 12) -> list:
    """Return a list of canton codes representing the top *n* cantons.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame produced by ``aggregate_by_canton`` with a ``canton`` column.
    n : int, optional
        Number of top cantons to return (default 12).

    Returns
    -------
    list
        Canton identifiers (as strings) sorted by descending total count.
    """
    if 'canton' not in df.columns:
        return []
    total_counts = df.groupby('canton')['count'].sum()
    top = total_counts.nlargest(n).index.tolist()
    return [str(c).strip() for c in top]
