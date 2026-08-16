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

Se sirven los tres modelos *pairwise* del pipeline Kedro (XGBoost, LightGBM y
el transformer de atención). El modelo en uso se elige **al arrancar** con la
variable de entorno `FLEET_LOADING_MODEL`; sin ella, el valor por defecto es
`xgboost`:

```bash
FLEET_LOADING_MODEL=attention fleet_loading/.venv/bin/python \
    -m uvicorn src.api.main:app --port 8000
```

El nombre debe coincidir con una carpeta de `artifacts/fleet_loading/`
(`xgboost`, `lightgbm` o `attention`). Si no existe, el servicio responde
`503` al primer uso. La API carga el modelo la primera vez que se pide
(*lazy*), así que el valor de la variable solo se lee en el arranque del
proceso; cambiarla requiere reiniciar.

Para confirmar cuál quedó activo:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"xgboost"}
```

La política de decodificación no se configura: se lee la registrada en los
resultados medidos de cada modelo (`artifacts/fleet_loading/results/*.json`)
y, si no existe, se usa `count` — el objetivo primario del caso de uso es
maximizar cuántos vehículos se transportan.

### Los otros modelos y por qué no se sirven

El repositorio entrena seis. Los otros tres quedan fuera por razones distintas:

| Modelo | Formulación | ¿Por qué no se sirve? |
|---|---|---|
| MLP (Keras) | *pairwise* | Es pairwise y serviría igual, pero requiere TensorFlow/Keras, que la API no carga (el entorno de servicio es el de `fleet_loading`). Su artefacto además vive en `artifacts/mlp/` con otro formato (`feature_schema.json` + `.keras`) que `ModelService` no lee. Es el candidato natural si algún día se quiere servir |
| Random Forest | ancho fijo | Clasificador multiclase con la flota rellenada a `max_trucks`; no generaliza por encima del rango de entrenamiento. Y su artefacto ni siquiera guarda el modelo (`artifacts/rf/` solo tiene el esquema y el reporte) |
| Regresión logística | ancho fijo | Igual que el RF: la flota rellenada a `max_trucks` le pone un tope duro que este servicio no aplica |

## Sin límite de camiones ni de capacidad

Los tres modelos servidos son *pairwise*: su eje de camiones es dinámico
(`None` en la arquitectura), así que la misma flota admite cualquier número de
camiones y cualquier capacidad sin reentrenar. Los clásicos (Random Forest y
regresión logística) **no** se sirven: su formulación de ancho fijo los acota
al rango de entrenamiento, y este servicio no aplica ese tope.
