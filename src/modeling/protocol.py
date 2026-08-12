"""src/modeling/protocol.py

Único lugar del proyecto donde se construye una partición de evaluación.

Por qué existe
--------------
Hasta ahora había dos protocolos distintos conviviendo:

* el MLP (`scripts/train_mlp.py`) usaba `split_by_time` — holdout temporal
  2018-2024 / 2025 / 2026;
* XGBoost, LightGBM y el transformer (el pipeline Kedro) usaban
  `GroupShuffleSplit(test_size=0.2, random_state=42)` — una partición
  aleatoria por episodio.

Las cifras de ambos se publicaron en la misma tabla comparativa, que por tanto
no compara lo mismo. El propio equipo lo había detectado (ver
`docs/decisiones/03_comparabilidad.md`) sin llegar a unificarlo.

Se unifica en la partición **temporal**, y no al revés, por dos razones:

1. Es la honesta para este problema. Un episodio es (cantón, semana ISO);
   semanas contiguas del mismo cantón son manifiestos casi gemelos. Una
   partición aleatoria los reparte a ambos lados y el modelo ve el futuro, lo
   que infla la métrica sin que sobreviva a datos nuevos.
2. Es lo que ya declara `config/mlp.yaml` y lo que describe el reporte.

Cómo se usa
-----------
Todo entrenamiento y toda evaluación llaman a `make_splits`. Todo `metrics.json`
lleva `protocol` y `split`, y `assert_comparable` impide construir una tabla
con filas medidas de formas distintas — que es exactamente el error que este
módulo existe para hacer imposible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.modeling.dataset import (
    DEFAULT_TEST_YEARS,
    DEFAULT_TRAIN_YEARS,
    DEFAULT_VAL_YEARS,
    assert_no_episode_leakage,
    drop_non_optimal,
    split_by_time,
    summarize_splits,
)


@dataclass(frozen=True)
class SplitConfig:
    """Años de cada partición. Los valores por defecto son los del proyecto."""

    train_years: tuple[int, ...] = DEFAULT_TRAIN_YEARS
    val_years: tuple[int, ...] = DEFAULT_VAL_YEARS
    test_years: tuple[int, ...] = DEFAULT_TEST_YEARS

    # Una partición vacía o casi vacía no es un error de programación sino de
    # configuración (p. ej. pedir un año que el dataset no cubre), y produce
    # métricas sin sentido en vez de fallar. Mejor que falle.
    min_episodes: int = 1

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> SplitConfig:
        """Construye desde el bloque `data:` de config/mlp.yaml o parameters.yml."""
        if not data:
            return cls()
        return cls(
            train_years=tuple(data.get("train_years", DEFAULT_TRAIN_YEARS)),
            val_years=tuple(data.get("val_years", DEFAULT_VAL_YEARS)),
            test_years=tuple(data.get("test_years", DEFAULT_TEST_YEARS)),
            min_episodes=int(data.get("min_episodes", 1)),
        )

    @property
    def protocol_id(self) -> str:
        """Identificador estable que se graba en cada `metrics.json`.

        Dos corridas son comparables si y sólo si coinciden en esta cadena.
        """

        def _rango(years: tuple[int, ...]) -> str:
            if not years:
                return "vacio"
            ys = sorted(years)
            return str(ys[0]) if len(ys) == 1 else f"{ys[0]}_{ys[-1]}"

        return (
            "temporal-"
            f"{_rango(self.train_years)}/{_rango(self.val_years)}/{_rango(self.test_years)}"
        )


@dataclass
class SplitBundle:
    """Particiones ya construidas, más lo que hace falta para reportarlas."""

    splits: dict[str, pd.DataFrame]
    config: SplitConfig
    n_episodes_non_optimal_dropped: int
    summaries: list = field(default_factory=list)

    @property
    def protocol_id(self) -> str:
        return self.config.protocol_id

    def __getitem__(self, name: str) -> pd.DataFrame:
        return self.splits[name]


def make_splits(joined: pd.DataFrame, config: SplitConfig | None = None) -> SplitBundle:
    """Construye train/val/test con el protocolo único del proyecto.

    Hace siempre, y en este orden:

    1. descarta episodios cuyo maestro agotó el presupuesto (`optimal=False`),
       porque su etiqueta no es el óptimo y no sirve ni de objetivo ni de
       referencia;
    2. reparte por año ISO;
    3. **verifica que ningún episodio caiga en dos particiones**. Esa
       comprobación ya existía en `dataset.py` pero no la llamaba nadie;
    4. falla si alguna partición queda por debajo de `min_episodes`.
    """
    config = config or SplitConfig()

    if "iso_year" not in joined.columns:
        raise ValueError(
            "make_splits necesita la columna 'iso_year'. Si vienes del pipeline "
            "Kedro, revisa que `encode_features` la conserve al hacer el join."
        )

    joined, dropped = drop_non_optimal(joined)
    splits = split_by_time(
        joined,
        train_years=config.train_years,
        val_years=config.val_years,
        test_years=config.test_years,
    )
    assert_no_episode_leakage(splits)

    summaries = summarize_splits(splits)
    for summary in summaries:
        if summary.n_episodes < config.min_episodes:
            raise ValueError(
                f"La partición '{summary.name}' quedó con {summary.n_episodes} episodios "
                f"(mínimo {config.min_episodes}). Años pedidos: "
                f"{getattr(config, f'{summary.name}_years')}."
            )

    return SplitBundle(
        splits=splits,
        config=config,
        n_episodes_non_optimal_dropped=dropped,
        summaries=summaries,
    )


def stamp(payload: dict[str, Any], config: SplitConfig, split: str) -> dict[str, Any]:
    """Marca un `metrics.json` con el protocolo y la partición reportada.

    Sin esta marca no hay forma de saber, mirando un artefacto, si es comparable
    con otro. Es la mitad del arreglo; la otra mitad es `assert_comparable`.
    """
    payload["protocol"] = config.protocol_id
    payload["split"] = split
    return payload


def assert_comparable(payloads: list[dict[str, Any]]) -> None:
    """Falla si las filas de una tabla comparativa no se midieron igual.

    Es la salvaguarda que impide que vuelva a ocurrir lo de la tabla de cinco
    modelos: mezclar holdout temporal con partición aleatoria y presentarlo como
    una comparación.
    """
    if not payloads:
        return

    faltantes = [p.get("model", "?") for p in payloads if "protocol" not in p or "split" not in p]
    if faltantes:
        raise ValueError(
            "Estos resultados no declaran protocolo/partición y no se pueden "
            f"comparar: {faltantes}. Fueron generados antes de la unificación; "
            "hay que regenerarlos."
        )

    combinaciones = {(p["protocol"], p["split"]) for p in payloads}
    if len(combinaciones) > 1:
        detalle = ", ".join(f"{p.get('model', '?')}={p['protocol']}@{p['split']}" for p in payloads)
        raise ValueError(
            f"Se intentó comparar resultados medidos con protocolos distintos: {detalle}. "
            "Vuelve a evaluar todos los modelos con el mismo protocolo."
        )
