# Alcance original (superado)

!!! warning "Diseño superado — se conserva como historia de la propuesta"
    Describe el diseño del 25 de junio de 2025: un asignador en **PyTorch**,
    **dos camiones** fijos y los archivos `src/loading/assigner.py`,
    `scripts/train_loading.py` y `scripts/eval_loading.py`, **ninguno de los
    cuales existe**. El sistema que se construyó es otro: cuatro modelos que
    puntúan pares `(vehículo, camión)` con eje de camiones dinámico.

    El alcance vigente está en [la propuesta](../propuesta/01_problem.md) y el
    diseño real en [estructura del código](../estructura.md).

**Last updated:** 2025-06-25

## Decisions

| Date | Decision |
|------|----------|
| 2025-06-25 | **Loading only** — no route sequencing (TSP). |
| 2025-06-25 | **Must train a model**; **no black-box** tools (no OR-Tools, pretrained transformers, RL frameworks). |
| 2025-06-25 | **Supervised imitation** — exhaustive loader labels small instances; PyTorch assigner on real SRI manifests. |
| 2025-06-25 | DRL, Pointer routing, simulator, OR-Tools → [deferred/](../propuesta/deferred/README.md). |

## In scope

* Capacitated **vehicle-to-truck assignment** and deferral under CU limits.
* Training episodes from **real SRI weekly manifests** (`data/clean/`).
* **Automatic labels** via exhaustive search (N ≤ ~20, 2 trucks × 6 CU).
* **PyTorch assigner** with capacity masking at inference.
* **Baselines** we implement: status-quo grouping, greedy first-fit.
* **Evaluation** on held-out SRI weeks (temporal split).

## Out of scope

* TSP / route distance minimization.
* DRL simulators and Pointer Networks for routing.
* OR-Tools, commercial MIP solvers, Stable-Baselines, pretrained embeddings.
* Claiming global optimality on large manifests at inference.

## Why train if exhaustive search exists?

Exhaustive search is tractable **only at small N** (offline teacher). Training is justified for:

1. **Scale gap** — labels on N ≤ ~20; inference on larger weekly manifests where search hits a time budget.
2. **Generalization** — assign loads on unseen SRI weeks without re-running search.
3. **Course requirement** — end-to-end trained model with transparent evaluation.

Do **not** claim ML is necessary at the same N where exhaustive search is already fast and exact.

## Pipeline

```
SRI CSV  →  weekly manifests
                ↓
        subsample if N > 20 (from that week)
                ↓
        exhaustive labeler  →  truck assignments
                ↓
        PyTorch assigner (train)
                ↓
        evaluate vs greedy / status quo / timed exhaustive
```

**Train/val split:** by time (e.g. train 2017–2024, validate 2025–2026).

## What we will not claim

* Optimal routing or total distance.
* Optimal loading on large N (feasible heuristic only).
* Random synthetic demand unrelated to SRI.

## Planned code (not yet implemented)

| Module | Role |
|--------|------|
| `src/loading/scenarios.py` | Build weekly manifests from cleaned CSVs |
| `src/loading/labeler.py` | Exhaustive optimal assignment (small N) |
| `src/loading/assigner.py` | PyTorch model |
| `scripts/train_loading.py` | Training loop |
| `scripts/eval_loading.py` | Baselines + metrics |
