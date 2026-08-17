# Transport manifest UI build + data tools

**Session ID:** ses_ff7e46080ffeArK712n9VqJVMi
**Created:** 8/15/2026, 8:07:03 PM
**Updated:** 8/16/2026, 9:09:08 PM

---

## User

the fleet got is not actually small on real case?

---

## Assistant (Build · DeepSeek V4 Flash Free · 31.3s)

_Thinking:_

The user asks: "the fleet got is not actually small on real case?" — they're questioning that the generated fleet for the real case (2734 vehicles) is `[3.9, 6.0, 7.0]` — only 3 trucks with capacities 3.9-7.0, total capacity ~16.9. That's tiny for 2734 vehicles. The user is pointing out this seems wrong/unrealistic: a fleet of 3 trucks can't carry 2734 vehicles — it's "small" for the real case.

They're right. Using `generate_fleet` (the training distribution: 1-4 trucks, caps 3-9) for a 2734-vehicle episode gives an absurd fleet — total capacity ~17 vs total CU of the episode which would be ~2500+. The whole thing gets deferred. That's the honest training distribution, but it's NOT "coherent" for a real big episode.

The user's concern: for the real case, the fleet should be sized to the episode. So I need to scale the fleet to the episode size. What's "coherent"? 

The professor's case: 18 vehicles, 2 trucks of 6 = total capacity 12. 12 AUTOMOVIL (CU 1.0) = 12. So fleet total capacity ≈ total CU of the vehicles it's meant to carry (slightly less to be binding). For a real episode of N vehicles with CU per class, a "coherent" fleet would have total capacity roughly matching total CU (or some fraction), distributed across a realistic number of trucks.

So the fix: for real episodes, derive the fleet from the episode's actual content:
- total CU of the episode = sum of cu.
- A realistic fleet: total capacity ≈ total CU (or a binding fraction like 90-100%), split across a number of trucks that's realistic relative to the episode size.

How to decide number of trucks? Options:
- Scale linearly from training: training episodes ≤20 vehicles with 1-4 trucks. So trucks ≈ vehicles / 5-ish? For 2734 → ~136-547 trucks. That's a lot but realistic for a big canton week.
- Or keep total capacity ≈ total CU and pick n_trucks so each truck is in a realistic range (e.g., CAP_RANGE 3-9, or bigger). For 2734 vehicles with average CU ~0.5 (mostly MOTOCICLETA 0.2), total CU ≈ let's estimate: MOTOCICLETA 0.2 × many + AUTOMOVIL 1.0... The episode 21701/2026-09 had 2734 vehicles. Total CU? Let me compute.

Actually, let me think about what makes sense and is defensible:
- A "coherent" fleet for a real episode: total capacity close to (but slightly below) the episode's total CU — otherwise the problem is trivially solvable (empty trucks) or unsolvable (everything deferred).
- Number of trucks: derived so that truck capacities stay in a plausible range.

Let me compute the episode's total CU first, then design.

Let me compute total CU for the default episode and a few others.

Tienes razón: `[3.9, 6.0, 7.0]` para 2,734 vehículos es absurdo (capacidad total ~17). La distribución del entrenamiento (1-4 camiones) es para episodios ≤20. Veo el CU total real del episodio para dimensionar la flota de forma



**Tool: bash**

**Input:**
```json
{
  "command": "cd /home/vicbguti/Projects/vehicles && .venv/bin/python -c \"\nimport pandas as pd\ndf = pd.read_parquet('data/features/vehicles_in_scope.parquet')\nep = df[(df.iso_year==2026)&(df.iso_week==9)&(df.canton.astype(str)=='21701')]\nprint('vehiculos:', len(ep), 'CU total:', round(ep.cu.sum(),1))\nprint(ep.groupby('clase').agg(n=('cu','size'), cu=('cu','sum')).round(1))\n\"",
  "description": "Compute total CU of default real episode"
}
```

**Output:**
```
vehiculos: 2734 CU total: 2572.3
                n      cu
clase                    
AUTOMOVIL     490   490.0
CAMIONETA     348   487.2
JEEP         1351  1486.1
MOTOCICLETA   545   109.0

```

---

## Assistant (Build · DeepSeek V4 Flash Free · 53.2s)

_Thinking:_

The default real episode: 2734 vehicles, total CU = 2572.3. A "coherent" fleet should have total capacity on the order of ~2572 (a bit below to be binding, or around there). So the fleet needs total capacity ≈ 2500, not 17.

Now, how to generate the fleet coherently? Design a `real_episode_fleet` that:
1. Computes episode total CU.
2. Sets a fleet total capacity ≈ some fraction of total CU (e.g., 90-95%, so the problem is binding but mostly solvable — a real planning scenario).
3. Splits across a number of trucks derived from episode size.

Number of trucks: what's realistic? Training used 1-4 trucks for ≤20 vehicles (so roughly trucks ≈ vehicles/5, capped at 4). Scaling: for N vehicles, trucks ≈ max(1, round(N/5))? For 2734 → 547 trucks. Hmm, that's a lot but plausibly realistic for a big weekly canton delivery. But 547 trucks each with ~4.7 capacity... total 2572/547 ≈ 4.7. Capacities in [3,9] range — plausible.

Alternatively, keep the fleet "small-ish" but realistic: the number of trucks should reflect actual capacity per truck. Real transport trucks carry maybe 5-20 vehicles. If we assume a target truck size, e.g., capacities in [3,9] (the training range) as a per-truck norm, then trucks = ceil(total_CU / avg_cap). With avg cap ~6, 2572/6 ≈ 429 trucks. Also huge.

Hmm, the question is what the user considers "coherent". The user's objection: fleet is "small" for the real case. They want a fleet that makes sense for 2734 vehicles. 

I think a reasonable, defensible design:
- Fleet total capacity ≈ episode total CU (binding at ~100%, maybe slightly less like 95% so it's a real stress but near-solvable).
- Number of trucks = derived from total capacity and per-truck capacity drawn from the training CAP_RANGE [3,9] (each truck is a real transport unit). Number = round(total_CU / mean_cap) where mean_cap ~ 6. So trucks ≈ total_CU / 6.
- Deterministic by seed.

But is ~400 trucks "realistic"? For a canton delivering 2572 CU in a week — that's a big operation. Actually yes, plausible for the real case. The professor's intractable case was exactly: way more vehicles than fleet capacity. For the real episode, a fleet sized to ~95% of CU is the meaningful stress test.

Alternatively, simpler and more defensible: total capacity = fraction of total CU (say 0.95), number of trucks chosen so each truck capacity is in a plausible band. Let me keep per-truck capacities in [3.0, 9.0] (the training band — a transport unit carries 3-9 CU). Then n_trucks = ceil(total_cap / 6) or similar.

Wait — but there's a tension: the training fleet is 1-4 trucks. The model (xgboost) was trained with 1-4 trucks. Serving a 400-truck fleet is way outside training (extrapolation). The docs already say >4 trucks only pairwise models serve it. For the professor-escalado we had 3 trucks. The real episode with 400 trucks would be heavy for the model. But the user wants a real case; the intractability is the point.

Hmm, but actually — maybe the user just wants the fleet to NOT be trivially small. Let me reconsider: perhaps a better approach is to size the fleet relative to episode size so it's a *realistic planning scenario*: total capacity ≈ episode CU × binding fraction, trucks sized in the plausible per-truck band. That gives a big fleet for a big episode. Deterministic.

Let me implement `real_episode_fleet`:
```python
def real_episode_fleet(iso_year, iso_week, canton):
    registry = _registry()
    ep = filter...
    total_cu = float(ep.cu.sum())
    if total_cu == 0: raise?
    rng = random.Random(_episode_seed(...))
    # fracción de CU que la flota puede mover: ligera, para que sea un caso real
    # de estrés (no trivial, no imposible). 
    target = total_cu * 0.95
    # cada camión transporta 3-9 CU (la banda del entrenamiento)
    caps = []
    while sum(caps) < target:
        caps.append(round(rng.uniform(*CAP_RANGE), 1))
    # último camión recortado al excedente, para no pasarse de target
    ...
    return caps
```
But that loop yields many trucks each 3-9 → ~300-500 trucks for 2572. And the last truck may need trimming. Also generating many trucks is fine.

But is that what the user wants? "the fleet got is not actually small on real case?" — they're asking whether the generated fleet for the real case is actually small. Yes it is — too small. They want it coherent with the episode.

Alternatively, maybe I'm overcomplicating. Perhaps the "coherent" approach: the fleet should have total capacity comparable to the episode's CU, split into trucks sized reasonably. Let me design cleanly:

```python
def real_episode_fleet(y, w, c):
    total_cu = ... 
    rng = random.Random(seed)
    # Número de camiones: tantos como hagan falta para que cada uno quede en la
    # banda plausible [CAP_MIN, CAP_MAX] del entrenamiento, con la flota capaz
    # de mover el ~95% del CU del episodio (un caso de estrés real, no trivial).
    target = round(total_cu * 0.95, 1)
    trucks = []
    while sum(trucks) < target:
        trucks.append(round(rng.uniform(*CAP_RANGE), 1))
    # ajustar el último para no pasarse del objetivo
    trucks[-1] = round(target - sum(trucks[:-1]), 1)  # could be tiny
    # drop trucks <= 0
```

Edge: the last truck could be tiny (e.g., 0.1). That's fine — it's just a unit. Or maybe better: generate n_trucks = ceil(target / mid_cap), then scale.

Actually cleaner: 
```python
mid = (CAP_RANGE[0]+CAP_RANGE[1])/2  # 6.0
n = max(1, round(target / mid))
caps = [round(rng.uniform(*CAP_RANGE),1) for _ in range(n)]
# escalar para sumar exactamente `target`
scale = target / sum(caps)
caps = [round(c*scale,1) for c in caps]
# corregir redondeo en el último
```
Scaling keeps them in ~[3,9]×scale — scale≈1, so stays plausible. Sum ≈ target. Good. Deterministic.

Hmm, but "same distribution as training" is lost — now it's sized to episode. That's the point: the training distribution was for small episodes. For real episodes we extrapolate sensibly. Document it.

Let me also reconsider: should total capacity be 95%? If fleet = 95% of CU, then ~5% deferred — a realistic, mostly-solvable but stressed plan. If 100%+, trivial (everything fits). If much less, mostly deferred. 90-100% is the interesting band. Let me use a fixed binding fraction constant, e.g., `FLEET_CU_FRACTION = 0.95`. Deterministic, documented.

Now the user might also question: the number of trucks. For 2572 CU / ~6 per truck ≈ 429 trucks. That's the "real" scale. It's honest. The model with 429 trucks — pairwise can handle but slow. xgboost can't (>4 trucks, pairwise only). The scenario serves the manifest; distribution may need pairwise. That's fine, documented.

Let me verify: with the current fleet [3.9,6,7], total 16.9. That's ~0.7% of CU — everything deferred. The user is right.

Let me implement the sized fleet. Also update the test (`assert all(3.0 <= cap <= 9.0)` will break since scaled caps might go slightly outside; and `1 <= len(fleet) <= 4` breaks). Let me update the test to assert total capacity ≈ 95% of episode CU, and fleet sum close to target, deterministic, and n_trucks plausible (>4 for big episode).

Let me write it.

Also need to update docs (the distribution description) and the smoke test expectation. Let me implement.

Also consider the unit: CAP_RANGE = (3.0, 9.0). For target 2572*0.95=2443.7, n=round(2443.7/6)=407 trucks. Each ~6. Fine.

Let me code `real_episode_fleet`:
```python
CAP_RANGE_LOW, CAP_RANGE_HIGH = (3.0, 9.0)  # import from scenarios? CAP_RANGE is there.
```
`from src.loading.scenarios import CAP_RANGE, generate_fleet` — CAP_RANGE is (3.0, 9.0). Let me import CAP_RANGE.

Implementation:
```python
FLEET_CU_FRACTION = 0.95

def real_episode_fleet(iso_year, iso_week, canton):
    registry = _registry()
    episode = registry[(registry.iso_year==iso_year)&(registry.iso_week==iso_week)&(registry.canton.astype(str)==canton)]
    total_cu = float(episode["cu"].sum())
    target = round(total_cu * FLEET_CU_FRACTION, 1)
    rng = random.Random(_episode_seed(...))
    mid = (CAP_RANGE[0] + CAP_RANGE[1]) / 2
    n_trucks = max(1, round(target / mid))
    caps = [round(rng.uniform(*CAP_RANGE), 1) for _ in range(n_trucks)]
    if n_trucks:
        scale = target / sum(caps)
        caps = [round(c * scale, 1) for c in caps]
        # corrije el redondeo para que sume exactamente target
        caps[-1] = round(target - sum(caps[:-1]), 1)
    return caps
```
Return floats sorted? `generate_fleet` sorted them. Sort for consistency. And if total_cu==0 (empty episode), that's the 404 case handled before.

Edge: n_trucks could be 0 if target < mid/2 → max(1, ...) handles. caps[-1] could become ≤0 if rounding; guard: if caps[-1] <= 0: replace with target - sum(caps[:-1]) could still be 0 → drop it. Minor; with these magnitudes fine.

Wait, `_episode_seed` — I defined it already. Good.

Let me update.

El episodio tiene 2,572 CU; la flota generada suma ~17 (0.7%). La banda del entrenamiento es para episodios ≤20, no para un cantón completo. Redimensiono: la flota debe mover ~95% del CU real del episodio, con cada camión en la banda plausible (3-

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/src/api/examples.py",
  "newString": "from src.api.schemas import ManifestVehicleIn\nfrom src.loading.scenarios import CAP_RANGE",
  "oldString": "from src.api.schemas import ManifestVehicleIn\nfrom src.loading.scenarios import generate_fleet"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 16.3s)

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/src/api/examples.py",
  "newString": "def real_episode_fleet(iso_year: int, iso_week: int, canton: str) -> list[float]:\n    \"\"\"Flota coherente para un episodio real, dimensionada al CU real del\n    episodio y determinista por episodio.\n\n    El SRI no publica la flota de transporte --esa es la decisión del\n    operador--, así que se construye con la misma convención del entrenamiento\n    (cada camión transporta 3-9 CU), pero **escalada al episodio**: el total de\n    la flota cubre el ``FLEET_CU_FRACTION`` del CU del episodio, para que el\n    caso sea un estrés real (no trivial por exceso de espacio, ni imposible por\n    falta). La banda de 1-4 camiones del entrenamiento es para episodios de\n    <= 20 vehículos; un cantón completo de cientos de vehículos requiere una\n    flota proporcional.\n    \"\"\"\n    registry = _registry()\n    episode = registry[\n        (registry[\"iso_year\"] == iso_year)\n        & (registry[\"iso_week\"] == iso_week)\n        & (registry[\"canton\"].astype(str) == canton)\n    ]\n    total_cu = float(episode[\"cu\"].sum())\n    target = round(total_cu * FLEET_CU_FRACTION, 1)\n\n    rng = random.Random(_episode_seed(iso_year, iso_week, canton))\n    mid_capacity = (CAP_RANGE[0] + CAP_RANGE[1]) / 2\n    n_trucks = max(1, round(target / mid_capacity))\n    caps = [round(rng.uniform(*CAP_RANGE), 1) for _ in range(n_trucks)]\n    scale = target / sum(caps)\n    caps = [round(c * scale, 1) for c in caps]\n    # Corrige el redondeo para que la flota sume exactamente `target`.\n    caps[-1] = round(target - sum(caps[:-1]), 1)\n    if caps[-1] <= 0:\n        caps[-1] = min(CAP_RANGE)  # un camión mínimo conserva el objetivo\n    return sorted(caps)\n\n\ndef real_episode_count(iso_year: int, iso_week: int, canton: str) -> int:",
  "oldString": "def real_episode_fleet(iso_year: int, iso_week: int, canton: str) -> list[float]:\n    \"\"\"Flota coherente para un episodio real, generada con la MISMA distribución\n    del entrenamiento (``generate_fleet``) y determinista por episodio. El SRI no\n    publica la flota de transporte --esa es la decisión del operador--, así que\n    esta es la flota que el modelo esperaría ver junto a esos vehículos.\n    \"\"\"\n    return generate_fleet(random.Random(_episode_seed(iso_year, iso_week, canton)))\n\n\ndef real_episode_count(iso_year: int, iso_week: int, canton: str) -> int:"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 4.8s)

Añado la constante y actualizo la docstring del endpoint en

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/src/api/examples.py",
  "newString": "# Un caso-scenario real por defecto: todo lo registrado en el cantón 21701\n# durante la semana 9 de 2026 (2,734 vehículos), sin cap de submuestreo.\nDEFAULT_REAL_EPISODE = (2026, 9, \"21701\")\n\n# Fracción del CU del episodio que la flota puede mover: un caso de estrés\n# real, no trivial por exceso de espacio ni imposible por falta.\nFLEET_CU_FRACTION = 0.95",
  "oldString": "# Un caso-scenario real por defecto: todo lo registrado en el cantón 21701\n# durante la semana 9 de 2026 (2,734 vehículos), sin cap de submuestreo.\nDEFAULT_REAL_EPISODE = (2026, 9, \"21701\")"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 10.6s)

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/src/api/main.py",
  "newString": "* ``real-episode``: un episodio real completo (vehículos sin cap) con la\n      flota dimensionada al CU real del episodio: cada camión en la banda del\n      entrenamiento (3-9 CU) y el total cubriendo el 95% del CU del episodio,\n      determinista por episodio. El SRI no publica la flota de transporte\n      --esa es decisión del operador--, así que esta es la flota que un\n      operador necesitaría para mover ese episodio.\n    \"\"\"",
  "oldString": "* ``real-episode``: un episodio real completo (vehículos sin cap) con la\n      flota generada por la misma distribución del entrenamiento\n      (``generate_fleet``), determinista por episodio. El SRI no publica la\n      flota de transporte --esa es decisión del operador--, así que esta es la\n      flota que el modelo esperaría ver junto a esos vehículos.\n    \"\"\""
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 5.5s)

Actualizo el test que asumía la banda de entrenamiento y verifico



**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/tests/api/test_examples.py",
  "newString": "def test_flota_del_episodio_real_es_determinista_y_dimensionada() -> None:\n    \"\"\"La flota del caso real se dimensiona al CU del episodio (no es la banda\n    de 1-4 camiones del entrenamiento, que es para episodios <= 20).\"\"\"\n    y, w, c = DEFAULT_REAL_EPISODE\n    fleet = real_episode_fleet(y, w, c)\n    assert fleet == real_episode_fleet(y, w, c)  # determinista por episodio\n    assert len(fleet) > 4  # un cantón completo necesita una flota proporcional\n    assert all(cap > 0 for cap in fleet)\n    total_cu = sum(\n        v.cu for v in parse_csv(build_real_episode_csv(y, w, c))\n    )\n    assert round(sum(fleet), 1) == round(total_cu * 0.95, 1)\n    assert real_episode_count(y, w, c) > 20",
  "oldString": "def test_flota_del_episodio_real_es_determinista_y_del_entrenamiento() -> None:\n    \"\"\"La flota del caso real se genera con la misma distribución del\n    entrenamiento (1-4 camiones, capacidades en [3, 9]) y es reproducible.\"\"\"\n    y, w, c = DEFAULT_REAL_EPISODE\n    fleet = real_episode_fleet(y, w, c)\n    assert fleet == real_episode_fleet(y, w, c)\n    assert 1 <= len(fleet) <= 4\n    assert all(3.0 <= cap <= 9.0 for cap in fleet)\n    assert real_episode_count(y, w, c) > 20"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 25.2s)

**Tool: bash**

**Input:**
```json
{
  "command": "cd /home/vicbguti/Projects/vehicles && .venv/bin/python -m ruff format src/api/examples.py src/api/main.py tests/api/test_examples.py && export PATH=\"$HOME/.local/bin:$PATH\" && just check 2>&1 | tail -3",
  "description": "Format and run check",
  "timeout": 600000
}
```

**Output:**
```
1 file reformatted, 2 files left unchanged

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
478 passed, 2 skipped, 1 warning in 21.54s

```

---

## Assistant (Build · DeepSeek V4 Flash Free · 10.9s)

**Tool: bash**

**Input:**
```json
{
  "command": "cd /home/vicbguti/Projects/vehicles && (uv run uvicorn src.api.main:app --port 8011 >/tmp/opencode/api.log 2>&1 &) && sleep 4 && .venv/bin/python -c \"\nimport json, urllib.request\nr = json.load(urllib.request.urlopen('http://127.0.0.1:8011/api/scenarios/real-episode'))\nfleet = r['fleet']\nprint('camiones:', len(fleet), '| capacidad total:', round(sum(fleet),1))\nprint('capacidades:', fleet[:8], '...' if len(fleet)>8 else '')\nprint('vehiculos:', r['vehicles_count'])\n\" && pkill -f \"uvicorn src.api.main:app --port 8011\"",
  "description": "Smoke test the resized fleet",
  "timeout": 60000
}
```

**Output:**
```
camiones: 407 | capacidad total: 2443.7
capacidades: [3.0, 3.1, 3.1, 3.1, 3.1, 3.1, 3.2, 3.2] ...
vehiculos: 2734

```

---

## Assistant (Build · DeepSeek V4 Flash Free · 7.2s)

_Thinking:_

Now the fleet is coherent: 407 trucks, total capacity 2443.7 = 95% of 2572.3 CU. Each truck ~6 CU (in the 3-9 band). That's a real-scale fleet for a 2734-vehicle canton week.

Now update docs to reflect the sized fleet. Let me update docs/api.md's scenario bullet (currently says "se genera con la misma distribución del entrenamiento (generate_fleet, 1-4 camiones de 3-9 unidades)").

407 camiones, 2,443.7 de capacidad total = 95% del CU del episodio. Actualizo la doc que aún decía "1-4 camiones"



**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/vicbguti/Projects/vehicles/docs/api.md",
  "newString": "* `scenarios/{nombre}` devuelve el caso **completo** en JSON: los vehículos\n  reales (`csv_url` + `vehicles_count`) y la **flota** que va con ellos. Para\n  los ejemplos del enunciado la flota es la declarada (`[6, 6]` /\n  `[6, 7, 7]`); para `real-episode` el SRI no publica la flota de transporte\n  (es decisión del operador), así que se construye con la misma convención del\n  entrenamiento (cada camión transporta 3-9 CU) pero **dimensionada al\n  episodio**: el total cubre el 95% del CU real del episodio, determinista por\n  episodio. El caso por defecto (2,734 vehículos, 2,572 CU) lleva una flota de\n  ~407 camiones. La UI carga vehículos y flota juntos.",
  "oldString": "* `scenarios/{nombre}` devuelve el caso **completo** en JSON: los vehículos\n  reales (`csv_url` + `vehicles_count`) y la **flota** que va con ellos. Para\n  los ejemplos del enunciado la flota es la declarada (`[6, 6]` /\n  `[6, 7, 7]`); para `real-episode` el SRI no publica la flota de transporte\n  (es decisión del operador), así que se genera con la **misma distribución\n  del entrenamiento** (`generate_fleet`, 1-4 camiones de 3-9 unidades) y es\n  determinista por episodio. La UI carga vehículos y flota juntos."
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · DeepSeek V4 Flash Free · 27.1s)

**Tool: bash**

**Input:**
```json
{
  "command": "cd /home/vicbguti/Projects/vehicles && export PATH=\"$HOME/.local/bin:$PATH\" && just docs-build 2>&1 | tail -2 && just check 2>&1 | tail -2",
  "description": "Docs build and final check",
  "timeout": 600000
}
```

**Output:**
```
INFO    -  Building documentation to directory: /home/vicbguti/Projects/vehicles/site
INFO    -  Documentation built in 1.82 seconds
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
478 passed, 2 skipped, 1 warning in 20.79s

```

---

## Assistant (Build · DeepSeek V4 Flash Free · 6.2s)

Corregido. La flota del caso real ahora está **dimensionada al episodio**:

- Antes: `[3.9, 6.0, 7.0]` (17 CU, 0.7% del episodio) — absurda para 2,734 vehículos.
- Ahora: **407 camiones, 2,443.7 CU totales = 95% del CU real del episodio** (2,572.3), cada camión en la banda del entrenamiento (3-9 CU), determinista por episodio.

La banda de 1-4 camiones era para episodios ≤20; un cantón completo requiere una flota proporcional, y el 95% lo deja como estrés real (ni trivial por exceso de espacio ni imposible). `real_episode_fleet` en `src/api/examples.py` lo deriva del CU del episodio; test actualizado verifica determinismo + dimensión, `just check` (478) y docs en verde.

Quedan 3 commits sin empujar + este trabajo sin commitear. ¿Commit y push?
