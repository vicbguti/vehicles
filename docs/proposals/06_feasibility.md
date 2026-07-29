# Episode & Labeler Feasibility

> **Auto-generated.** Reproduce with:
> ```bash
> python3 scripts/loading/episode_feasibility.py
> ```

**Generated:** 2026-06-25 16:19 UTC  
**Data:** `data/clean/SRI_Vehiculos_Nuevos_*.csv` (all available years)  
**Skipped years (no `FECHA PROCESO` column):** 2017  
**Script:** `scripts/loading/episode_feasibility.py`

---

## Method

### Columns used

| Field | CSV column (2024 example) | Purpose |
|-------|---------------------------|---------|
| Process date | `FECHA PROCESO (DD/MM/AA)` or `(MM/DD/AA)` in 2018–2019 | ISO year-week episode boundary (`dayfirst` set per column) |
| Canton | `CANTÓN` | Canton ID for canton-week episodes |
| Class | `CLASE` | Vehicle class (CU mapping in pipeline) |

### Episode definitions measured

1. **National week** — all registrations in Ecuador in ISO week *w* of year *y*.
2. **Canton-week** — registrations in canton *c* during week (*y*, *w*).

These are **not** the same as a single distributor's port manifest (see [Quality](#quality-vs-toy-scenario) below).

### Thresholds

Fraction of episodes with vehicle count N ≤ threshold (target labeler: N ≤ ~20).

---

## National week (all registrations)

| Year | Rows | Weeks | Median N/week | Min | Max |
|------|------|-------|---------------|-----|-----|
| 2018 | 355,304 | 51 | 6763 | 2912 | 14225 |
| 2019 | 366,354 | 50 | 7068 | 2906 | 15788 |
| 2020 | 167,716 | 38 | 5106 | 96 | 7305 |
| 2021 | 219,329 | 37 | 5927 | 229 | 8988 |
| 2022 | 247,163 | 37 | 6753 | 245 | 9118 |
| 2023 | 261,455 | 37 | 6950 | 2677 | 10312 |
| 2024 | 367,583 | 51 | 6936 | 894 | 14428 |
| 2025 | 436,602 | 51 | 8386 | 2603 | 17173 |
| 2026 | 164,503 | 17 | 9957 | 4822 | 16199 |

### Pooled national weeks (all years in run)

- Episodes: **369**
- Median N: **6804**
- Mean N: **7008**

| Threshold | Episodes | % |
|-------------|----------|---|
| ≤ 10 | 0 | 0.0% |
| ≤ 15 | 0 | 0.0% |
| ≤ 18 | 0 | 0.0% |
| ≤ 20 | 0 | 0.0% |
| ≤ 25 | 0 | 0.0% |
| ≤ 50 | 0 | 0.0% |
| ≤ 100 | 1 | 0.3% |

**Finding:** National weeks are always large (thousands per week). Episodes with N ≤ 20 **do not occur** without subsampling.

---

## Canton-week (canton × ISO week)

- Episodes: **50,106**
- Median N: **9**
- 90th percentile: **103**

| Threshold | Episodes | % |
|-------------|----------|---|
| ≤ 10 | 26,487 | 52.9% |
| ≤ 15 | 30,385 | 60.6% |
| ≤ 18 | 32,102 | 64.1% |
| ≤ 20 | 33,104 | 66.1% |
| ≤ 25 | 35,225 | 70.3% |
| ≤ 50 | 40,724 | 81.3% |
| ≤ 100 | 44,956 | 89.7% |

**Finding:** ~half of canton-weeks have N ≤ 15; ~60% have N ≤ 20. High **volume** of naturally small episodes.

---

## Labeler compute

### Assignment search space

Each vehicle → Truck 1, Truck 2, or Defer ⇒ **3^N** assignments (capacity pruning reduces explored nodes).

| N | 3^N (naive upper bound) |
|---|-------------------------|
| 10 | 59,049 |
| 15 | 14,348,907 |
| 18 | 387,420,489 |
| 20 | 3,486,784,401 |
| 25 | 847,288,609,443 |

### Sample timing (pruned DFS, development prototype)

Method: depth-first search with capacity pruning in `episode_feasibility.py`.
A production labeler in `src/loading/labeler.py` should use tighter bounds (see deferred theory docs).

- **N=10** (6 sedans + 4 SUVs): 10 vehicles loaded, 8.02 CU total, **30.90 ms**
- **N=15–20:** not timed here — requires optimized labeler before batch labeling.

**Status:** exhaustive labeling at N≤20 is *expected* tractable with a proper solver; **not yet implemented** for batch runs.

### Grouping-only timing (toy N=16)

For the small toy scenario (selecting 16 from 18 and packing into 2 trucks) the grouping-only search space is **89,760** configurations — see deferred theory [`7_complexity.md`](deferred/theory/1_search_space/7_complexity.md). Example runtimes:

- At **1 million evaluations/second**: $$\frac{89,760}{10^{6}} \approx \mathbf{0.09\ \text{seconds}}.$$\
- At **1 trillion evaluations/second**: $$\frac{89,760}{10^{12}} \approx \mathbf{90\ \text{nanoseconds}}.$$

This confirms that enumeration of grouping assignments is trivial at that toy size; routing (TSP) is the dominant factor that makes full joint search intractable.

---

## Volume estimate (if subsampling)

If each national week yields **k** random subsamples of fixed N=18 (stratified by class/canton):

- k=5: ~205 episodes/year × years in run
- k=10: ~410 episodes/year × years in run
- k=20: ~820 episodes/year × years in run

Subsampling adds volume but each slice is an arbitrary subset of national flow — see quality notes.

---

## Quality vs toy scenario

| Definition | Volume | Match to [example/problem/scenario.md](./example/problem/scenario.md) |
|------------|--------|------------------------------------------------------------------------|
| National week | High | **Poor** — ~7k vehicles/week, not an 18-vehicle port manifest |
| Canton-week | High (N≤20 common) | **Weak** — single canton, not multi-destination shipment |
| Subsample N=18 from week | Tunable | **Medium** — real class/canton mix, artificial batch boundary |
| Toy 18-vehicle case | n=1 | **Exact** — for labeler sanity check only |

**Status:** Episode definition for training is **not finalized**. This report supplies data to choose one.

---

## Open items

- [ ] Pick episode definition and document in [03_data.md](./03_data.md)
- [ ] Implement `src/loading/labeler.py` and replicate Case 3 in [example/solution/comparisons.md](./example/solution/comparisons.md)
- [ ] Re-run this script after episode filter (e.g. Guayas-only, class filter) is chosen
