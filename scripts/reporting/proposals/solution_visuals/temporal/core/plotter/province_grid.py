# -*- coding: utf-8 -*-
"""Province‑level wrapper for canton‑class grid visualisation.
It filters the full canton DataFrame to the subset belonging to a given
province and then delegates to :func:`plot_canton_class_grid`.
"""
from typing import List
import pandas as pd

from .canton_class_grid import plot_canton_class_grid


def plot_province_grid(
    df: pd.DataFrame,
    canton_codes: List[str],
    out_path: str,
    province_name: str | None = None,
) -> None:
    """Create a canton‑class grid for all cantons of *province*.

    Parameters
    ----------
    df: pd.DataFrame
        Full DataFrame produced by the canton aggregation step.
    canton_codes: list[str]
        List of canton identifiers that belong to the province.
    out_path: str
        Destination PNG file.
    province_name: str, optional
        Human‑readable province name used for the figure title.
    """
    if not canton_codes:
        # Nothing to plot – create an empty placeholder to avoid errors.
        print(f"No cantons found for province {province_name!r}, skipping plot.")
        return
    # Filter the DataFrame to the relevant cantons.
    sub_df = df[df["canton"].isin(canton_codes)]
    # Re‑use the existing grid function; it will handle title per canton.
    plot_canton_class_grid(sub_df, cantons=canton_codes, out_path=out_path)
    # Optionally, add a global title (the existing function does not provide one).
    # This could be enhanced by modifying ``plot_canton_class_grid`` to accept a
    # ``figure_title`` argument, but keeping it simple preserves backward
    # compatibility.
    print(f"Province‑level canton‑class visual saved to {out_path}")
