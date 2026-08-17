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
| `/api/distribute` | `POST` | Genera el plan de distribución para los vehículos aceptados, con el **modelo usado** y **cuánto tardó** |

`/api/manifest` acepta el CSV del operador en `csv` (punto y coma o coma) o la
lista ya estructurada en `vehicles`. En ambos casos hay que pasar `fleet`, las
capacidades de los camiones. Devuelve cada vehículo con `status` `accepted` o
`rejected` y, cuando aplica, el `reason` del caso de uso: `Sin Datos`,
`Sin Almacenamiento`, `Sin Cantón` o `Supera la capacidad máxima`.

`/api/distribute` recibe los vehículos aceptados y la flota, y devuelve el plan:
camiones (orden canónico, capacidad descendente) con sus vehículos, más la
sección `sin_camion` con los que el modelo difiere por falta de espacio.

## Cuánto tardó y con qué modelo

Ambos `POST` cronometran su trabajo y lo devuelven en la respuesta, para poder
comparar el coste en tiempo de los seis modelos sobre el mismo manifiesto:

| Campo | En | Qué mide |
|---|---|---|
| `elapsed_ms` | `/api/manifest` | La validación. No interviene el modelo, así que son décimas de milisegundo |
| `elapsed_ms` | `/api/distribute` | La inferencia y la decodificación del plan |
| `model` | `/api/distribute` | Con qué modelo se resolvió, sin tener que consultar `/api/health` aparte |

El cronómetro de `/api/distribute` arranca **después** de resolver la
dependencia del servicio, así que no incluye la carga del artefacto —que
ocurre una sola vez, en el primer uso.

Aun así, **la primera petición no es comparable**: el calentamiento perezoso de
torch, Keras y la caché de página del sistema la encarecen mucho. Medido sobre
el mismo manifiesto de 8 vehículos y una flota de dos camiones de 6:

| Modelo | Primera petición | Peticiones siguientes |
|---|---|---|
| XGBoost | 27.8 ms | ~20 ms |
| LightGBM | 17.4 ms | ~2.9 ms |
| Transformer | 817.6 ms | ~7.5-8.9 ms |

Son cifras indicativas de una máquina y una corrida, no una medición
controlada: sirven para ver el orden de magnitud del calentamiento, no para
declarar un ganador. Lo que sí muestran es que la primera medición hay que
descartarla —el transformer pasa de 818 ms a menos de 9—. El frontend lo
advierte junto a los tiempos por el mismo motivo.

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

## Probar con manifiestos de ejemplo

El input del app son CSV, y la propia app los sirve: `GET
/api/manifests/{nombre}.csv` devuelve un manifiesto de ejemplo (cabeceras
`identificador;clase;cu;canton`, punto y coma) construido **con vehículos
reales del SRI** (registro `data/features/vehicles_in_scope.parquet`, 2.5 M de
vehículos con su código real, cantón y CU), que es el objetivo del proyecto.
El resultado se envía tal cual a `POST /api/distribute`.

```bash
# El ejemplo del profesor (18 vehículos, 2 camiones de 6 unidades) y su
# escalado a 25 vehículos en 3 camiones (6, 7, 7)
curl http://127.0.0.1:8000/api/manifests/profesor.csv
curl http://127.0.0.1:8000/api/manifests/profesor-escalado.csv

# Un caso-scenario real: todos los vehículos registrados en el cantón 21701
# durante la semana 9 de 2026 (2,734 vehículos), sin cap de submuestreo
curl http://127.0.0.1:8000/api/manifests/real-episode.csv
```

* `real-episode.csv` es un **episodio real completo** del SRI: el registro
  (año, semana, cantón) tal cual, sin el cap de <= 20 vehículos por episodio
  que aplica la generación de episodios de entrenamiento
  (`src/loading/scenarios.py`). Se puede pedir cualquier episodio del registro
  con `?iso_year=&iso_week=&canton=`; por defecto sirve el cantón 21701,
  semana 9 de 2026 (2,734 vehículos). Los episodios reales van de 1 a 2,774
  vehículos, así que este es el caso de estrés real del problema.

* El preset `profesor` reproduce la forma del ejemplo de intratabilidad del
  enunciado (18 vehículos, 2 clases, 2 camiones de 6): Sedán -> AUTOMOVIL y
  SUV -> JEEP (las clases que entrena el proyecto), con los CU reales del SRI
  (1.0 y 1.1) en lugar de la abstracción del enunciado (2/3 y 1.0).
  `profesor-escalado` es el mismo caso a 25 vehículos en 3 camiones (6, 7, 7).
* La flota no va en el CSV: se envía en el cuerpo del `POST /api/distribute`
  (`[6, 6]` para `profesor`, `[6, 7, 7]` para `profesor-escalado`).
* Las filas se modelan con el mismo esquema pydantic que valida el API
  (`ManifestVehicleIn`), de modo que el CSV siempre vuelve a entrar por
  `parse_csv`. Los tests (`tests/api/test_examples.py`) crean estos
  manifiestos como fixtures de pytest y verifican el round trip completo
  contra el API (`TestClient` de FastAPI).
* El resto de pruebas con manifiestos propios (cualquier composición de
  clases y flota) se puede hacer subiendo un CSV propio a
  `POST /api/manifest` (validación) o `POST /api/distribute` (plan).
* Cada corrida anota su procedencia (semillas, episodios, cantones y flota) en
  un `.provenance.json` junto al CSV, o por stderr si se imprime a stdout —
  para que un manifiesto de prueba sea reproducible.
