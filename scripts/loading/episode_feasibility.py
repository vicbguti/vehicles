#!/usr/bin/env python3
"""Profile SRI episode sizes for fleet-loading label feasibility.

Writes a reproducible markdown report to:
  reports/03_proposals/fleet_routing/06_feasibility.md

Usage (from repo root):
  python3 scripts/loading/episode_feasibility.py
  python3 scripts/loading/episode_feasibility.py --years 2023 2024
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "clean"
REPORT_PATH = REPO_ROOT / "reports" / "03_proposals/fleet_routing" / "06_feasibility.md"

TRUCK_CAPACITY = 6.0
THRESHOLDS = (10, 15, 18, 20, 25, 50, 100)


def locate_column(columns: list[str], candidates: list[str]) -> str | None:
    upper = {c.upper(): c for c in columns}
    for cand in candidates:
        if cand.upper() in upper:
            return upper[cand.upper()]
    return None


def load_year_frame(csv_path: Path) -> pd.DataFrame | None:
    head = pd.read_csv(csv_path, sep=";", encoding="latin1", nrows=0)
    cols = head.columns.tolist()
    date_col = locate_column(
        cols,
        [
            "FECHA PROCESO (DD/MM/AAAA)",
            "FECHA PROCESO (DD/MM/AA)",
            "FECHA PROCESO (MM/DD/AA)",
        ],
    )
    canton_col = locate_column(cols, ["CANTÓN", "CANTON", "Codigo Canton"])
    if not date_col:
        return None  # e.g. 2017 uses month-only columns; skipped

    usecols = [date_col, "CLASE"] if "CLASE" in cols else [date_col, "Clase"]
    class_col = usecols[1]
    if canton_col:
        usecols.append(canton_col)

    df = pd.read_csv(csv_path, sep=";", encoding="latin1", usecols=usecols)
    df = df.rename(columns={date_col: "fecha", class_col: "clase"})
    if canton_col:
        df = df.rename(columns={canton_col: "canton"})
    dayfirst = "MM/DD" not in date_col.upper()
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=dayfirst, errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["iso_year"] = df["fecha"].dt.isocalendar().year.astype(int)
    df["iso_week"] = df["fecha"].dt.isocalendar().week.astype(int)
    return df


def threshold_table(series: pd.Series, thresholds: tuple[int, ...]) -> list[str]:
    lines = []
    total = len(series)
    for t in thresholds:
        n = int((series <= t).sum())
        pct = 100.0 * n / total if total else 0.0
        lines.append(f"| ≤ {t} | {n:,} | {pct:.1f}% |")
    return lines


def best_loading_dfs(cu_weights: list[float], capacity: float = TRUCK_CAPACITY) -> tuple[int, float]:
    """Pruned DFS: max vehicles loaded on 2 trucks (no defer required in scoring)."""
    n = len(cu_weights)
    best_loaded = 0
    best_util = -1.0

    def dfs(i: int, loads: list[float], loaded: int) -> None:
        nonlocal best_loaded, best_util
        if i == n:
            util = sum(loads)
            if loaded > best_loaded or (loaded == best_loaded and util > best_util):
                best_loaded = loaded
                best_util = util
            return
        cu = cu_weights[i]
        for truck in (0, 1, 2):  # 0, 1 = trucks; 2 = defer
            if truck == 2:
                dfs(i + 1, loads, loaded)
                continue
            new_load = loads[truck] + cu
            if new_load > capacity + 1e-9:
                continue
            loads[truck] = new_load
            dfs(i + 1, loads, loaded + 1)
            loads[truck] -= cu

    dfs(0, [0.0, 0.0], 0)
    return best_loaded, best_util


def benchmark_labeler() -> list[str]:
    """Quick timing at small N; larger N documented as combinatorial bound only."""
    lines = [
        "## Labeler compute",
        "",
        "### Assignment search space",
        "",
        "Each vehicle → Truck 1, Truck 2, or Defer ⇒ **3^N** assignments (capacity pruning reduces explored nodes).",
        "",
        "| N | 3^N (naive upper bound) |",
        "|---|-------------------------|",
    ]
    for n in (10, 15, 18, 20, 25):
        lines.append(f"| {n} | {3**n:,} |")

    weights10 = [0.67] * 6 + [1.0] * 4
    t0 = time.perf_counter()
    loaded, util = best_loading_dfs(weights10)
    ms = (time.perf_counter() - t0) * 1000

    lines.extend([
        "",
        "### Sample timing (pruned DFS, development prototype)",
        "",
        "Method: depth-first search with capacity pruning in `episode_feasibility.py`.",
        "A production labeler in `src/loading/labeler.py` should use tighter bounds (see deferred theory docs).",
        "",
        f"- **N=10** (6 sedans + 4 SUVs): {loaded} vehicles loaded, {util:.2f} CU total, **{ms:.2f} ms**",
        "- **N=15–20:** not timed here — requires optimized labeler before batch labeling.",
        "",
        "**Status:** exhaustive labeling at N≤20 is *expected* tractable with a proper solver; **not yet implemented** for batch runs.",
        "",
    ])
    return lines


def analyze_years(years: list[int] | None) -> str:
    files = sorted(DATA_DIR.glob("SRI_Vehiculos_Nuevos_*.csv"))
    if years:
        files = [f for f in files if any(str(y) in f.name for y in years)]
    if not files:
        raise SystemExit(f"No CSV files found in {DATA_DIR}")

    national_weekly_parts: list[pd.Series] = []
    canton_weekly_parts: list[pd.Series] = []
    year_summaries: list[str] = []
    skipped: list[str] = []

    for csv_path in files:
        year = int(csv_path.stem.split("_")[-1])
        df = load_year_frame(csv_path)
        if df is None:
            skipped.append(str(year))
            continue
        national = df.groupby(["iso_year", "iso_week"]).size()
        national_weekly_parts.append(national)
        year_summaries.append(
            f"| {year} | {len(df):,} | {len(national)} | {national.median():.0f} | {national.min()} | {national.max()} |"
        )
        if "canton" in df.columns:
            canton_week = df.groupby(["iso_year", "iso_week", "canton"]).size()
            canton_weekly_parts.append(canton_week)

    national_all = pd.concat(national_weekly_parts)
    canton_all = pd.concat(canton_weekly_parts) if canton_weekly_parts else pd.Series(dtype=int)

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    years_label = ", ".join(str(y) for y in years) if years else "all available years"

    lines = [
        "# Episode & Labeler Feasibility",
        "",
        "> **Auto-generated.** Reproduce with:",
        "> ```bash",
        "> python3 scripts/loading/episode_feasibility.py",
        "> ```",
        "",
        f"**Generated:** {generated}  ",
        f"**Data:** `data/clean/SRI_Vehiculos_Nuevos_*.csv` ({years_label})  ",
        f"**Skipped years (no `FECHA PROCESO` column):** {', '.join(skipped) if skipped else 'none'}  ",
        "**Script:** `scripts/loading/episode_feasibility.py`",
        "",
        "---",
        "",
        "## Method",
        "",
        "### Columns used",
        "",
        "| Field | CSV column (2024 example) | Purpose |",
        "|-------|---------------------------|---------|",
        "| Process date | `FECHA PROCESO (DD/MM/AA)` or `(MM/DD/AA)` in 2018–2019 | ISO year-week episode boundary (`dayfirst` set per column) |",
        "| Canton | `CANTÓN` | Canton ID for canton-week episodes |",
        "| Class | `CLASE` | Vehicle class (CU mapping in pipeline) |",
        "",
        "### Episode definitions measured",
        "",
        "1. **National week** — all registrations in Ecuador in ISO week *w* of year *y*.",
        "2. **Canton-week** — registrations in canton *c* during week (*y*, *w*).",
        "",
        "These are **not** the same as a single distributor's port manifest (see [Quality](#quality-vs-toy-scenario) below).",
        "",
        "### Thresholds",
        "",
        "Fraction of episodes with vehicle count N ≤ threshold (target labeler: N ≤ ~20).",
        "",
        "---",
        "",
        "## National week (all registrations)",
        "",
        "| Year | Rows | Weeks | Median N/week | Min | Max |",
        "|------|------|-------|---------------|-----|-----|",
        *year_summaries,
        "",
        "### Pooled national weeks (all years in run)",
        "",
        f"- Episodes: **{len(national_all):,}**",
        f"- Median N: **{national_all.median():.0f}**",
        f"- Mean N: **{national_all.mean():.0f}**",
        "",
        "| Threshold | Episodes | % |",
        "|-------------|----------|---|",
        *threshold_table(national_all, THRESHOLDS),
        "",
        "**Finding:** National weeks are always large (thousands per week). Episodes with N ≤ 20 **do not occur** without subsampling.",
        "",
        "---",
        "",
        "## Canton-week (canton × ISO week)",
        "",
    ]

    if len(canton_all):
        lines.extend([
            f"- Episodes: **{len(canton_all):,}**",
            f"- Median N: **{canton_all.median():.0f}**",
            f"- 90th percentile: **{canton_all.quantile(0.9):.0f}**",
            "",
            "| Threshold | Episodes | % |",
            "|-------------|----------|---|",
            *threshold_table(canton_all, THRESHOLDS),
            "",
            "**Finding:** ~half of canton-weeks have N ≤ 15; ~60% have N ≤ 20. High **volume** of naturally small episodes.",
        ])
    else:
        lines.append("*Canton column not found — canton-week stats skipped.*")

    lines.extend([
        "",
        "---",
        "",
        *benchmark_labeler(),
        "---",
        "",
        "## Volume estimate (if subsampling)",
        "",
        "If each national week yields **k** random subsamples of fixed N=18 (stratified by class/canton):",
        "",
    ])

    weeks_per_year = national_all.groupby(level=0).count().mean() if len(national_all) else 0
    for k in (5, 10, 20):
        lines.append(f"- k={k}: ~{weeks_per_year * k:.0f} episodes/year × years in run")

    lines.extend([
        "",
        "Subsampling adds volume but each slice is an arbitrary subset of national flow — see quality notes.",
        "",
        "---",
        "",
        "## Quality vs toy scenario",
        "",
        "| Definition | Volume | Match to [example/problem/scenario.md](./example/problem/scenario.md) |",
        "|------------|--------|------------------------------------------------------------------------|",
        "| National week | High | **Poor** — ~7k vehicles/week, not an 18-vehicle port manifest |",
        "| Canton-week | High (N≤20 common) | **Weak** — single canton, not multi-destination shipment |",
        "| Subsample N=18 from week | Tunable | **Medium** — real class/canton mix, artificial batch boundary |",
        "| Toy 18-vehicle case | n=1 | **Exact** — for labeler sanity check only |",
        "",
        "**Status:** Episode definition for training is **not finalized**. This report supplies data to choose one.",
        "",
        "---",
        "",
        "## Open items",
        "",
        "- [ ] Pick episode definition and document in [03_data.md](./03_data.md)",
        "- [ ] Implement `src/loading/labeler.py` and replicate Case 3 in [example/solution/comparisons.md](./example/solution/comparisons.md)",
        "- [ ] Re-run this script after episode filter (e.g. Guayas-only, class filter) is chosen",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile SRI episode sizes for loading feasibility.")
    parser.add_argument("--years", type=int, nargs="*", help="Years to include (default: all CSV files)")
    args = parser.parse_args()

    report = analyze_years(args.years)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
