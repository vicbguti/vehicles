# -*- coding: utf-8 -*-
"""Helper functions for data aggregation used by visualisation plotters.

These functions are deliberately internal to the visualisation package and are
not part of the public API. They provide clean, testable logic for aggregating
counts per date and per arbitrary group keys.
"""

from __future__ import annotations

import pandas as pd
from typing import List, Tuple, Dict

def _aggregate_series(cls_df: pd.DataFrame, dates: List) -> pd.Series:
    """Aggregate counts for a single class over the provided dates.

    Parameters
    ----------
    cls_df: pd.DataFrame
        Sub‑frame containing rows for a single ``class`` (or any other grouping).
    dates: list
        Ordered list of date identifiers (e.g. strings) to re‑index the result.

    Returns
    -------
    pd.Series
        Series indexed by ``dates`` with missing dates filled with ``0``.
    """
    return (
        cls_df.groupby("date_label")["count"].sum().reindex(dates, fill_value=0)
    )

def _aggregate_series_multi(
    cls_df: pd.DataFrame, dates: List, group_by: List[str]
) -> Dict[Tuple, pd.Series]:
    """Aggregate counts for each combination of ``group_by`` over ``dates``.

    The return type maps the grouping key tuple to a ``pd.Series`` indexed by the
    supplied ``dates``.
    """
    result: Dict[Tuple, pd.Series] = {}
    for keys, grp in cls_df.groupby(group_by):
        key = (keys,) if not isinstance(keys, tuple) else keys
        result[key] = (
            grp.groupby("date_label")["count"].sum().reindex(dates, fill_value=0)
        )
    return result
