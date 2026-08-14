"""src/modeling/flat_features.py

Aplana los tensores de `src.modeling.features` a una fila fija por vehículo,
para modelos multiclase nativos de scikit-learn (RandomForest, regresión
logística multinomial) que no aceptan el eje de camiones dinámico que usan el
MLP y las GBTs (`(V, T, 19)`, `T` variable).

Por qué existe este módulo aparte de `features.py`
----------------------------------------------------
`build_model_arrays` en `features.py` produce un tensor *pairwise*: una fila
por `(vehículo, camión)` con el eje de camiones dejado como `None`, para que el
mismo modelo acepte cualquier número de camiones en inferencia. Ni
`RandomForestClassifier` ni `LogisticRegression` aceptan eso -- son
clasificadores de `K` clases fijas: reciben `X` de ancho constante y predicen
un único índice entre `0..K-1`.

La alternativa aquí es rellenar (*pad*) la flota a un tamaño fijo
`max_trucks` y tratar cada posición canónica (camión 1 = mayor capacidad, ...,
camión `max_trucks` = menor) como una columna de features más, en vez de un
eje del modelo. Consecuencia aceptada, no un descuido: a diferencia del MLP y
las GBTs, este modelo **no generaliza a flotas con más de `max_trucks`
camiones** en inferencia -- lanza `ValueError` en vez de fallar en silencio.
Es una limitación conocida, no un problema en este dataset: `N_TRUCKS_RANGE =
(1, 4)` en `src/loading/scenarios.py` fija ese tope en el propio maestro, así
que ningún episodio (entrenamiento, validación o prueba) lo excede.

El target (`canonical_target_index`, ya calculado en cada `EpisodeTensors` por
`features.build_episode_tensors`) no cambia: `0 = SIN_CAMION`, `1..T` el
camión canónico. Por eso `FlatArrays` es deliberadamente compatible con la
firma que espera `src.modeling.metrics.evaluate_model` (atributos
`episode_index` y `target`): las métricas de dominio (tasa de violación de
capacidad, brecha de vehículos cargados, etc.) se calculan con exactamente el
mismo código que usan el MLP y las GBTs, decodificando las probabilidades del
modelo con `capacity_decoder.decode_episode`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.modeling.features import (
    CONTEXT_BLOCK,
    TRUCK_BLOCK,
    VEHICLE_BLOCK,
    BlockScaler,
    EpisodeTensors,
    feature_names,
)


@dataclass(frozen=True)
class FlatArrays:
    """Una fila por vehículo, lista para `model.fit(X, target)`.

    `episode_index` y `target` usan los mismos nombres que
    `features.ModelArrays`, por compatibilidad con `src.modeling.metrics`.
    """

    X: np.ndarray  # (N, D) float32
    target: np.ndarray  # (N,) int32 -- 0 = SIN_CAMION, 1..T = camión canónico
    episode_index: np.ndarray  # (N,) int32 -- posición en la lista de episodios
    episode_ids: list[str]

    @property
    def n_rows(self) -> int:
        return self.X.shape[0]

    @property
    def n_features(self) -> int:
        return self.X.shape[1]


def flat_feature_names(classes: list[str], max_trucks: int) -> list[str]:
    """Nombres de columna de `FlatArrays.X`, en el mismo orden que `build_flat_arrays`."""
    names = feature_names(classes)
    truck_names = names[TRUCK_BLOCK]
    padded_truck_names = [
        f"camion_{k + 1}_{name}" for k in range(max_trucks) for name in truck_names
    ]
    return [*names[VEHICLE_BLOCK], *names[CONTEXT_BLOCK], *padded_truck_names]


def build_flat_arrays(
    episodes: list[EpisodeTensors], scaler: BlockScaler, max_trucks: int
) -> FlatArrays:
    """Aplana una lista de episodios a `FlatArrays`.

    `max_trucks` debe ser >= el máximo `n_trucks` de CUALQUIER partición que se
    vaya a construir con este mismo `scaler` (train/val/test), no sólo la que
    se está aplanando ahora -- de lo contrario val/test tendrían un ancho de
    columnas distinto al de entrenamiento. Se calcula una sola vez en el
    script de entrenamiento sobre las tres particiones combinadas.
    """
    if not episodes:
        raise ValueError("No hay episodios que aplanar.")

    vehicle_dim = episodes[0].vehicle.shape[1]
    truck_dim = episodes[0].truck.shape[1]
    context_dim = len(episodes[0].context)
    feature_dim = vehicle_dim + context_dim + max_trucks * truck_dim
    n_rows = sum(e.n_vehicles for e in episodes)

    X = np.zeros((n_rows, feature_dim), dtype=np.float32)
    target = np.zeros(n_rows, dtype=np.int32)
    episode_index = np.zeros(n_rows, dtype=np.int32)

    cursor = 0
    for ep_i, ep in enumerate(episodes):
        if ep.n_trucks > max_trucks:
            raise ValueError(
                f"El episodio {ep.episode_id} tiene {ep.n_trucks} camiones y el "
                f"relleno es de {max_trucks}."
            )
        v = scaler.transform(VEHICLE_BLOCK, ep.vehicle)  # (n_v, Dv)
        t = scaler.transform(TRUCK_BLOCK, ep.truck)  # (n_t, Dt)
        g = scaler.transform(CONTEXT_BLOCK, ep.context[None, :])[0]  # (Dg,)

        truck_padded = np.zeros(max_trucks * truck_dim, dtype=np.float64)
        truck_padded[: ep.n_trucks * truck_dim] = t.reshape(-1)

        n_v = ep.n_vehicles
        rows = slice(cursor, cursor + n_v)
        X[rows] = np.concatenate(
            [
                v,
                np.broadcast_to(g, (n_v, g.shape[0])),
                np.broadcast_to(truck_padded, (n_v, truck_padded.shape[0])),
            ],
            axis=1,
        ).astype(np.float32)
        target[rows] = ep.target
        episode_index[rows] = ep_i
        cursor += n_v

    return FlatArrays(
        X=X,
        target=target,
        episode_index=episode_index,
        episode_ids=[e.episode_id for e in episodes],
    )
