# Servicio de distribución (API)

El planificador se sirve también como una API HTTP (FastAPI) en `src/api/`.
Recibe un manifiesto y una flota, valida el primero con las alternativas del
caso de uso de entrada y devuelve el plan de distribución producido por el
modelo entrenado.

## Puesta en marcha

La API reutiliza la maquinaria del repositorio (`src.modeling` y
`fleet_loading`), así que se ejecuta con el mismo entorno que entrena los
modelos:

```bash
fleet_loading/.venv/bin/python -m uvicorn src.api.main:app --port 8000
```

Se sirve en `http://127.0.0.1:8000`. La documentación interactiva de los
esquemas queda en `/docs` (Swagger UI) y `/redoc`.

## Endpoints

| Ruta | Método | Qué hace |
|---|---|---|
| `/api/health` | `GET` | Estado del servicio y **modelo en uso** |
| `/api/manifest` | `POST` | Valida el manifiesto (CSV crudo o lista) contra la flota y devuelve el estado por vehículo |
| `/api/distribute` | `POST` | Genera el plan de distribución para los vehículos aceptados |

`/api/manifest` acepta el CSV del operador en `csv` (punto y coma o coma) o la
lista ya estructurada en `vehicles`. En ambos casos hay que pasar `fleet`, las
capacidades de los camiones. Devuelve cada vehículo con `status` `accepted` o
`rejected` y, cuando aplica, el `reason` del caso de uso: `Sin Datos`,
`Sin Almacenamiento`, `Sin Cantón` o `Supera la capacidad máxima`.

`/api/distribute` recibe los vehículos aceptados y la flota, y devuelve el plan:
camiones (orden canónico, capacidad descendente) con sus vehículos, más la
sección `sin_camion` con los que el modelo difiere por falta de espacio.

## Qué modelo responde

Se sirven los **seis modelos** del repositorio. El modelo en uso se elige **al
arrancar** con la variable de entorno `FLEET_LOADING_MODEL`; sin ella, el valor
por defecto es `xgboost`:

```bash
FLEET_LOADING_MODEL=mlp fleet_loading/.venv/bin/python \
    -m uvicorn src.api.main:app --port 8000
```

Los nombres válidos son `xgboost`, `lightgbm`, `attention` (en
`artifacts/fleet_loading/`), `mlp` (en `artifacts/mlp/`), y `rf` y `logreg`
(en `artifacts/<modelo>/`). Si el nombre no existe, el servicio responde `503`
al primer uso. La API carga el modelo la primera vez que se pide (*lazy*), así
que el valor de la variable solo se lee en el arranque del proceso; cambiarla
requiere reiniciar.

Para confirmar cuál quedó activo:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"xgboost"}
```

La política de decodificación no se configura: se lee la registrada en los
resultados medidos de cada modelo (`artifacts/fleet_loading/results/*.json`,
`artifacts/mlp/metrics.json`, o el propio `feature_schema.json` para los
clásicos) y, si no existe, se usa `count` — el objetivo primario del caso de
uso es maximizar cuántos vehículos se transportan.

### El MLP: mismo rol, distinto cargador

El MLP es *pairwise* y consume los mismos tensores canónicos, pero puntúa el
lote completo (`pair_features`, `defer_features`, `mask_bias`) y devuelve
logits crudos, igual que `scripts/evaluate_mlp.py`. Requiere **Keras**: si el
entorno de servicio no tiene TensorFlow, se usa el backend de torch (ya
presente). El artefacto vive en `artifacts/mlp/` con su propio formato
(`feature_schema.json` + `model.keras`), que `ModelService` ya lee.

### RF y regresión logística: de ancho fijo, con tope aplicado

Los dos clásicos sí se sirven, con una limitación honesta: son clasificadores
multiclase que rellenan la flota a `max_trucks` (4 en los artefactos
versionados), así que **solo responden flotas de hasta ese número de camiones**.
El servicio aplica el tope explícitamente:

* Con una flota dentro del rango, la distribución es idéntica a la de los
  pairwise (mismo `decode_episode`, misma garantía de factibilidad).
* Con más camiones, `POST /api/distribute` responde `422` con un mensaje que
  explica la limitación y sugiere un modelo pairwise, en vez de devolver un
  plan inválido.

El artefacto de RF (`artifacts/rf/model.joblib`) es regenerable con
`scripts/train_classical.py` y está en `.gitignore` por diseño; el binario se
genera localmente para servirlo (ver `docs/estructura.md`).

## Sin límite de camiones ni de capacidad

Los modelos *pairwise* servidos (XGBoost, LightGBM, attention, MLP) tienen el
eje de camiones dinámico (`None` en la arquitectura), así que la misma flota
admite **cualquier número de camiones y cualquier capacidad** sin reentrenar.
RF y regresión logística son de ancho fijo: su tope real (`max_trucks`) es
parte del artefacto y lo aplica el propio servicio.

## Probar con manifiestos propios

`scripts/sample_manifest.py` genera un CSV de prueba listo para el API
(cabeceras `identificador;clase;cu;canton`, punto y coma) muestreando
vehículos reales de `data/episodes/episode_vehicles.parquet` y construyendo la
flota con `src.loading.scenarios.make_fleet`, el mismo código del conjunto de
extrapolación:

```bash
# Un episodio real (año-semana-cantón) con 8 vehículos y una flota de 6
# camiones, con la misma capacidad total que una flota de 4 (extrapolación)
fleet_loading/.venv/bin/python scripts/sample_manifest.py \
    --vehicles 8 --trucks 6 --cap-mode constant-total

# Una semana grande (300 vehículos) con 10 camiones, guardado a archivo
fleet_loading/.venv/bin/python scripts/sample_manifest.py \
    --vehicles 300 --trucks 10 --out data/examples/manifiesto_10.csv
```

* `--vehicles 5..20` es **un episodio real completo** (una semana y un cantón
  del SRI, submuestreado a 5-20 por el generador de escenarios); por debajo
  del piso no existen episodios reales, y por encima el generador mezcla
  varios episodios (una semana real en los archivos limpios tiene cientos de
  vehículos).
* `--trucks` acepta **cualquier** número: hasta 4 replica el rango de
  entrenamiento; más allá es extrapolación (`same` = misma distribución de
  capacidad, `constant-total` = mismo espacio total repartido entre más
  camiones). Con más de 4 camiones solo los modelos pairwise lo sirven.
* Cada corrida anota su procedencia (semillas, episodios, cantones y flota) en
  un `.provenance.json` junto al CSV, o por stderr si se imprime a stdout —
  para que un manifiesto de prueba sea reproducible.
