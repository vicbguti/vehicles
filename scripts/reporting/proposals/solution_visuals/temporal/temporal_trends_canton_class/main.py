# -*- coding: utf-8 -*-
"""Entry point for the temporal trends canton‑class visualisation workflow.
This module wires together configuration loading, aggregation, summarisation
and plotting. It replaces the previous monolithic script while preserving
backward‑compatible behaviour (the package ``__init__`` re‑exports ``main``).
"""
import os
import sys

# Ensure all parent packages are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))

import pandas as pd

from temporal_trends_canton_class.config import load_config

# Aggregation utilities
from temporal.core.aggregator.by_canton import aggregate_by_canton
from utils.geo_mapper.mapper import code_to_province
from temporal.core.aggregator.by_province import aggregate_by_province
from temporal.core.aggregator.summary import top_n_cantons

# Plotting functions
from visualisation import plot_canton_class_grid, plot_province_grid


def main() -> None:
    # ---------------------------------------------------------------------
    # 1. Load configuration (fallback to defaults if config file missing).
    # ---------------------------------------------------------------------
    cfg = load_config()
    base_dir = cfg["data"]["base_dir"]
    # ---------------------------------------------------------------------
    # 2. Aggregate raw CSV data per canton.
    # ---------------------------------------------------------------------
    canton_agg = aggregate_by_canton(base_dir, cfg)
    # Convert the aggregation dict to a tidy DataFrame for plotting.
    df = pd.DataFrame(
        [
            {
                "year": k[0],
                "month": k[1],
                "canton": k[2],
                "class": k[3],
                "sub_class": k[4],
                "type": k[5],
                "count": v,
            }
            for k, v in canton_agg.items()
        ]
    )
    # Ensure a proper date label for the x‑axis.
    df["date_label"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str), format="%Y-%m")
    df["date_label"] = df["date_label"].dt.strftime("%Y-%m")

    # ---------------------------------------------------------------------
    # 3. Top‑12 national grid.
    # ---------------------------------------------------------------------
    top12_cantons = top_n_cantons(df)
    out_top12 = cfg["output"]["top12"]
    plot_canton_class_grid(df, cantons=top12_cantons, out_path=out_top12)

    # ---------------------------------------------------------------------
    # 4. Province‑specific grids.
    # ---------------------------------------------------------------------
    province_agg = aggregate_by_province(base_dir, cfg)
    # Build a DataFrame similar to the canton one but grouped by province.
    prov_df = pd.DataFrame(
        [
            {"year": k[0], "month": k[1], "province": k[2], "count": v}
            for k, v in province_agg.items()
        ]
    )
    prov_df["date_label"] = pd.to_datetime(
        prov_df["year"].astype(str) + "-" + prov_df["month"].astype(str), format="%Y-%m"
    ).dt.strftime("%Y-%m")
    # The existing ``plot_canton_class_grid`` expects the same column layout as the
    # canton DataFrame, so we reuse the provincial aggregation only for organising
    # output folders – each province gets its own grid of all cantons belonging to
    # that province.
    out_dir = cfg["output"]["by_province_dir"]
    os.makedirs(out_dir, exist_ok=True)
    # For each province, filter the original canton‑level DataFrame.
    for province in prov_df["province"].unique():
        province_cantons = (
            df[df["canton"].apply(lambda c: code_to_province(str(c)) == province)]["canton"].unique().tolist()
        )
        out_path = os.path.join(out_dir, f"{province}_canton_class.png")
        plot_province_grid(df, province_cantons, out_path, province_name=province)

if __name__ == "__main__":
    main()
