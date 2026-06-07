# -*- coding: utf-8 -*-
"""Validation helpers for visualisation plotters.

These functions keep the orchestrator thin and provide reusable checks.
"""

from __future__ import annotations

import pandas as pd

_REQUIRED_COLUMNS = {"date_label", "canton", "class", "sub_class", "type", "count"}


def validate_canton_grid_input(df: pd.DataFrame, cantons: list | None) -> pd.DataFrame:
    """Validate the input DataFrame for the canton‑class grid.

    * Ensures all required columns are present.
    * Applies an optional canton filter.
    * Raises a clear ``ValueError`` if the result is empty.

    Parameters
    ----------
    df : pd.DataFrame
        Raw data frame.
    cantons : list | None
        Optional list of canton identifiers to keep.

    Returns
    -------
    pd.DataFrame
        The validated (and possibly filtered) DataFrame.
    """
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame is missing required columns: {sorted(missing)}")

    if cantons is not None:
        df = df[df["canton"].isin(cantons)]
    if df.empty:
        raise ValueError("No data available for the selected cantons after validation.")
    return df
