#!/usr/bin/env python3
"""Entrena RandomForest o regresión logística multinomial (índice canónico fijo).

    data/episodes/episodes.parquet + episode_vehicles.parquet
            -> join, descarte de episodios no-óptimos, partición temporal
            -> canonicalización de la flota por capacidad (src.modeling.features)
            -> una fila por vehículo, flota rellenada a --max-trucks (src.modeling.flat_features)
            -> búsqueda de hiperparámetros con Optuna, cada intento logueado a MLflow
            -> mejor modelo: métricas de dominio (src.modeling.metrics) + artifacts/<model>/

A diferencia del MLP y las GBTs de `fleet_loading` (eje de camiones dinámico,
`(V, T, 19)`), este script entrena un clasificador multiclase estándar de
scikit-learn: la flota se rellena a un tamaño fijo y el modelo predice
directamente el índice canónico (`0 = SIN_CAMION`, `1..max_trucks` el camión).
Es la formulación que corresponde a "regresión logística multinomial" en
sentido estricto (softmax sobre clases fijas) y al uso nativo de
`RandomForestClassifier`. Ver `src/modeling/flat_features.py` para el porqué.

Uso (desde la raíz del repositorio):
    uv run python scripts/train_classical.py --model rf
    uv run python scripts/train_classical.py --model logreg --n-trials 100
    uv run python scripts/train_classical.py --model rf --tracking-uri sqlite:////content/drive/MyDrive/vehicles-mlflow/mlflow.db

En Colab: montar Drive, clonar el repo, `pip install -q scikit-learn optuna
mlflow pyarrow`, y pasar `--tracking-uri` apuntando a un archivo dentro de
Drive para que el tracking persista entre sesiones.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402

from src.modeling.capacity_decoder import POLICIES, decode_episode  # noqa: E402
from src.modeling.dataset import (  # noqa: E402
    assert_no_episode_leakage,
    drop_non_optimal,
    load_episode_tables,
    split_by_episode_hash,
    split_by_time,
    summarize_splits,
)
from src.modeling.features import BlockScaler, build_all_episodes  # noqa: E402
from src.modeling.figures import (  # noqa: E402
    PRESENTACION,
    etiquetas_canonicas,
    plot_confusion_matrix,
    plot_curves,
    write_history,
)
from src.modeling.flat_features import (  # noqa: E402
    FlatArrays,
    build_flat_arrays,
    flat_feature_names,
)
from src.modeling.metrics import (  # noqa: E402
    aggregate,
    build_result,
    episode_logits,
    evaluate_greedy,
)
from src.pipeline.transformation.derived_fields import VehicleClassConfig  # noqa: E402

DEFAULT_EPISODES_DIR = REPO_ROOT / "data" / "episodes"
CLASS_CONFIG_PATH = REPO_ROOT / "config" / "vehicle_classes.yaml"
DEFAULT_TRACKING_URI = f"sqlite:///{REPO_ROOT / 'mlflow.db'}"

MODEL_NAMES = ("rf", "logreg")

# Hiperparámetros que no se buscan -- se fijan por conocimiento del dominio
# (desbalance de clases documentado en docs/decisiones/01_hallazgos_transversales.md
# punto 5) o por estabilidad numérica, y se aplican tanto en cada intento de
# Optuna como en el reentrenamiento final del mejor trial.
RF_FIXED = dict(class_weight="balanced", n_jobs=-1, random_state=42)
LOGREG_FIXED = dict(max_iter=2000, random_state=42)


# ------------------------------------------------------------------ búsqueda
def suggest_rf_params(trial) -> dict:
    return dict(
        n_estimators=trial.suggest_int("n_estimators", 100, 800, step=50),
        max_depth=trial.suggest_int("max_depth", 4, 30),
        min_samples_split=trial.suggest_int("min_samples_split", 2, 20),
        min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
        max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    )


def suggest_logreg_params(trial) -> dict:
    solver = trial.suggest_categorical("solver", ["lbfgs", "saga"])
    # lbfgs sólo admite L2 puro (l1_ratio=0); saga admite el rango completo
    # [0, 1] (0=L2, 1=L1, intermedio=elastic-net) -- búsqueda condicional.
    # `penalty` (l1/l2 como string) está deprecado desde sklearn 1.8 a favor de
    # `l1_ratio`: pasar penalty="l1" con el l1_ratio=0.0 por defecto produce un
    # UserWarning de "Inconsistent values" y NO aplica L1 -- se detectó al
    # correr el smoke test contra sklearn 1.9. `l1_ratio` es la API vigente.
    l1_ratio = trial.suggest_float("l1_ratio", 0.0, 1.0) if solver == "saga" else 0.0
    return dict(
        C=trial.suggest_float("C", 1e-4, 1e2, log=True),
        solver=solver,
        l1_ratio=l1_ratio,
        class_weight=trial.suggest_categorical("class_weight", ["balanced", None]),
        # sklearn >=1.5 usa pérdida multinomial (softmax) por defecto con estos
        # solvers cuando hay más de 2 clases -- el flag explícito
        # `multi_class="multinomial"` está deprecado (eliminado en 1.7), así
        # que no se pasa.
    )


def suggest_params(model_name: str, trial) -> dict:
    return suggest_rf_params(trial) if model_name == "rf" else suggest_logreg_params(trial)


def fixed_extras(model_name: str) -> dict:
    return dict(RF_FIXED) if model_name == "rf" else dict(LOGREG_FIXED)


def finalize_params(model_name: str, best_params: dict) -> dict:
    """Reconstruye los hiperparámetros completos del trial ganador.

    `study.best_params` sólo trae las claves que Optuna efectivamente sugirió
    en ESE trial -- si ganó `solver="lbfgs"`, la clave `"l1_ratio"` nunca se
    sugirió (es condicional a `solver="saga"` en `suggest_logreg_params`) y no
    aparece. Se completa aquí con el mismo default, en vez de reproducir la
    búsqueda con un trial ficticio.
    """
    params = dict(best_params)
    if model_name == "logreg" and "l1_ratio" not in params:
        params["l1_ratio"] = 0.0
    return {**params, **fixed_extras(model_name)}


# Un `RandomForestClassifier` no expone su tamaño en bytes sin serializarlo, así
# que se decide por el número de nodos, que sí es barato de contar y es lo que
# manda: los 1,4 GB del bosque publicado son ~500 árboles de profundidad 26.
MAX_NODOS_MLFLOW = 2_000_000


def _cabe_en_mlflow(modelo, model_name: str) -> bool:
    """¿Merece la pena registrar el binario en MLflow, o es demasiado grande?

    Se mide en vez de decidirlo por nombre de modelo: un RF de 50 árboles poco
    profundos sí cabe, y una regla `if model_name == "rf"` lo excluiría igual.
    """
    if model_name != "rf":
        return True
    nodos = sum(int(e.tree_.node_count) for e in modelo.estimators_)
    return nodos <= MAX_NODOS_MLFLOW


def build_model(model_name: str, params: dict):
    if model_name == "rf":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(**params)
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(**params)


# ---------------------------------------------------------- curva de convergencia
#
# Ni el Random Forest ni la regresión logística tienen «época», así que eran los
# dos únicos modelos del proyecto sin curva de entrenamiento. Sí tienen un eje de
# convergencia propio --árboles e iteraciones de lbfgs--, análogo a la ronda de
# boosting de los GBT, y cada uno declara el suyo en el CSV.
#
# La forma de recorrerlo NO es la misma para los dos, y confundirlas cuesta
# calidad del modelo publicado:
#
#   * **Random Forest**: `warm_start` es exacto. Los árboles se acumulan en el
#     mismo bosque, así que crecerlo en diez tramos da un objeto bit a bit igual
#     al de un solo ajuste (fijado en tests/test_train_classical.py) y la curva
#     sale gratis.
#
#   * **Regresión logística**: `warm_start` NO sirve. lbfgs pierde su
#     aproximación del Hessiano en cada reanudación, así que diez tramos de 200
#     iteraciones rinden mucho menos que 2.000 seguidas: medido sobre los datos
#     reales, los diez tramos terminan SIN converger --cada uno agota su límite--
#     y dan un modelo peor (log-loss de validación 0,3990 frente a 0,3982,
#     macro-F1 0,8120 frente a 0,8137, coeficientes de norma media 2,34 frente a
#     3,34: infra-ajustado). Publicar eso para poder dibujar una curva sería
#     degradar el modelo a cambio de una figura.
#
#     Así que cada punto es un ajuste **independiente** con presupuesto creciente
#     --«¿a dónde llega lbfgs con 200 iteraciones? ¿y con 400?»--, que es además
#     lo que la curva dice que muestra. El último punto usa el presupuesto
#     completo, o sea que ES el modelo de un ajuste único, y como lbfgs converge
#     en ~776 iteraciones los presupuestos mayores repiten ese mismo modelo.
TRAMOS = 10

# Las evaluaciones intermedias se hacen sobre una muestra fija de entrenamiento.
# `predict_proba` de 500 árboles sobre las 444.051 filas, diez veces, domina el
# coste; 50.000 filas dan la misma forma de curva. La validación va entera: es la
# partición que se publica y no admite muestreo.
MUESTRA_CURVA = 50_000


def _eje_y_tramos(model_name: str, params: dict) -> tuple[str, str, list[int]]:
    """`(step_unit, hiperparámetro que crece, presupuestos crecientes)`.

    Los valores son acumulados --50, 100, ... 500 árboles-- porque son también lo
    que va a la columna `step` del CSV: el eje de la gráfica tiene que estar en
    árboles o en iteraciones, no en «número de tramo», o mentiría por un factor
    de 50. El último es siempre el presupuesto completo, sin repetirlo.
    """
    clave = "n_estimators" if model_name == "rf" else "max_iter"
    unidad = "n_trees" if model_name == "rf" else "lbfgs_iter"
    total = int(params[clave])
    paso = max(1, total // TRAMOS)
    acumulados = list(range(paso, total + 1, paso))[:TRAMOS]
    if acumulados[-1] != total:
        acumulados.append(total)
    return unidad, clave, acumulados


def ajustar_con_curva(model_name: str, params: dict, train, val, seed: int):
    """`(modelo final, filas de la curva, step_unit, presupuestos)`.

    El modelo devuelto es siempre el del presupuesto completo, así que la curva
    termina exactamente en el modelo que se publica: no hay un segundo ajuste por
    detrás que pueda divergir de lo que muestra la figura.
    """
    import warnings

    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import f1_score, log_loss

    step_unit, clave, tramos = _eje_y_tramos(model_name, params)
    acumula = model_name == "rf"  # ver el comentario de arriba
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(train.target), size=min(MUESTRA_CURVA, len(train.target)), replace=False)
    X_tr, y_tr = train.X[idx], train.target[idx]

    modelo = build_model(model_name, {**params, clave: tramos[0], "warm_start": acumula})
    filas = []
    for i, valor in enumerate(tramos):
        if acumula:
            modelo.set_params(**{clave: valor})
        else:
            # Ajuste nuevo por presupuesto, no reanudación.
            modelo = build_model(model_name, {**params, clave: valor})
        with warnings.catch_warnings():
            # sklearn desaconseja `class_weight="balanced"` con `warm_start`
            # «si los datos ajustados difieren del conjunto completo». Aquí nunca
            # difieren --siempre se ajusta el train entero--, así que los pesos
            # salen idénticos en cada tramo y el bosque resultante es bit a bit
            # el de un ajuste único. Comprobado en tests/test_train_classical.py.
            warnings.filterwarnings("ignore", message=".*class_weight presets.*")
            # Los presupuestos intermedios no convergen a propósito: ése es el
            # punto de la curva. Sólo interesa la advertencia del último, que si
            # aparece significa que el modelo publicado se quedó corto.
            if i < len(tramos) - 1:
                warnings.simplefilter("ignore", ConvergenceWarning)
            modelo.fit(train.X, train.target)

        fila = {}
        for nombre, X, y in (("", X_tr, y_tr), ("val_", val.X, val.target)):
            proba = modelo.predict_proba(X)
            fila[f"{nombre}loss"] = float(log_loss(y, proba, labels=modelo.classes_))
            fila[f"{nombre}macro_f1"] = float(
                f1_score(y, modelo.classes_[proba.argmax(axis=1)], average="macro", zero_division=0)
            )
        filas.append(fila)
        print(
            f"  {step_unit}={valor:<5} loss={fila['loss']:.4f} val_loss={fila['val_loss']:.4f} "
            f"macro_f1={fila['macro_f1']:.4f} val={fila['val_macro_f1']:.4f}"
        )

    # `warm_start` era un medio para dibujar la curva, no una propiedad del
    # modelo publicado: se deja como lo dejaría un ajuste normal.
    modelo.set_params(warm_start=False)
    return modelo, filas, step_unit, tramos


# ------------------------------------------------------------- métricas de dominio
def domain_metrics_for_split(
    model, episodes: list, flat: FlatArrays, n_classes: int, policy: str
) -> dict:
    """Decodifica las probabilidades del modelo y agrega con `src.modeling.metrics`.

    `flat` ya expone `episode_index`/`target` con la firma que espera las
    funciones de `src.modeling.metrics`, así que las métricas de dominio
    (violación de capacidad, brecha de vehículos cargados, F1 macro, matriz de
    confusión, ...) se calculan con el mismo código que usan el MLP y las
    GBTs -- no hay una segunda implementación de las métricas para este modelo.
    """
    logits = model.predict_proba(flat.X)  # (N, 1 + max_trucks), orden canónico
    max_labels = logits.shape[1]

    results = []
    for ep_i, ep in enumerate(episodes):
        rows = np.flatnonzero(flat.episode_index == ep_i)
        decoded = decode_episode(
            episode_logits(logits, rows, ep.n_trucks),
            cu=ep.cu,
            capacities=ep.capacities,
            policy=policy,
        )
        results.append(build_result(ep, decoded, flat.target[rows], n_classes))
    return aggregate(results, max_labels)


def select_policy(model, episodes: list, flat: FlatArrays, n_classes: int) -> str:
    """Elige la política del decodificador por validación (brecha de carga mínima)."""
    best, best_gap = "count", float("inf")
    for policy in POLICIES:
        m = domain_metrics_for_split(model, episodes, flat, n_classes, policy)
        if m["loaded_gap_mean"] < best_gap:
            best, best_gap = policy, m["loaded_gap_mean"]
    return best


# ---------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_NAMES, required=True)
    parser.add_argument("--episodes-dir", type=Path, default=DEFAULT_EPISODES_DIR)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--split", choices=("time", "hash"), default="time")
    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument(
        "--refit-from",
        type=Path,
        default=None,
        metavar="training_report.json",
        help="Reajusta con los `best_params` de un informe anterior y salta Optuna. "
        "La búsqueda del RF costó 100 min y 50 intentos; volver a pagarla sólo para "
        "regenerar curvas o artefactos no tiene sentido, y además cambiaría los "
        "hiperparámetros publicados. Por omisión (sin la bandera) se busca de cero.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Paralelismo de Optuna entre intentos (no confundir con el n_jobs=-1 "
        "interno de RandomForest). Default 1 para no sobre-suscribir CPUs: cada "
        "árbol ya usa todos los cores. Súbelo sólo para logreg, que no paraleliza "
        "internamente.",
    )
    parser.add_argument("--tracking-uri", default=DEFAULT_TRACKING_URI)
    parser.add_argument("--experiment-name", default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = args.out_dir or (REPO_ROOT / "artifacts" / args.model)
    out_dir.mkdir(parents=True, exist_ok=True)
    experiment_name = args.experiment_name or f"vehicles-{args.model}"

    import mlflow
    import mlflow.sklearn
    import optuna

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(experiment_name)

    # --- Datos ---------------------------------------------------------------
    joined = load_episode_tables(
        args.episodes_dir / "episodes.parquet",
        args.episodes_dir / "episode_vehicles.parquet",
    )
    joined, n_non_optimal = drop_non_optimal(joined)

    splits = split_by_time(joined) if args.split == "time" else split_by_episode_hash(joined)
    assert_no_episode_leakage(splits)
    summaries = summarize_splits(splits)
    for s in summaries:
        if s.n_rows == 0:
            raise SystemExit(
                f"La partición '{s.name}' quedó vacía. Con la muestra de humo use "
                "--split hash: los 200 episodios caen todos en 2018-W02."
            )

    classes = sorted(VehicleClassConfig.from_yaml(str(CLASS_CONFIG_PATH)).in_scope_classes)
    episodes = {name: build_all_episodes(df, classes) for name, df in splits.items()}

    max_trucks = max(e.n_trucks for eps in episodes.values() for e in eps)
    n_classes = len(classes)
    n_labels = max_trucks + 1

    scaler = BlockScaler.fit(episodes["train"], classes)
    flat = {name: build_flat_arrays(eps, scaler, max_trucks) for name, eps in episodes.items()}
    feat_names = flat_feature_names(classes, max_trucks)

    print(f"Modelo: {args.model}   Clases: {classes}   Camiones máximos: {max_trucks}")
    for s in summaries:
        print(
            f"  {s.name:<5} episodios={s.n_episodes:>7,}  filas={s.n_rows:>8,}  "
            f"diferidos={s.n_deferred_rows:>7,} ({s.deferred_pct:.2f}%)  años={list(s.years)}"
        )

    # --- Búsqueda de hiperparámetros ------------------------------------------
    train, val = flat["train"], flat["val"]

    def objective(trial: optuna.Trial) -> float:
        from sklearn.metrics import accuracy_score, f1_score

        params = {**suggest_params(args.model, trial), **fixed_extras(args.model)}
        with mlflow.start_run(run_name=f"{args.model}_trial_{trial.number}", nested=True):
            mlflow.log_params(params)
            model = build_model(args.model, params).fit(train.X, train.target)
            pred = model.predict(val.X)
            val_accuracy = accuracy_score(val.target, pred)
            val_macro_f1 = f1_score(val.target, pred, average="macro", zero_division=0)
            mlflow.log_metrics({"val_raw_accuracy": val_accuracy, "val_macro_f1": val_macro_f1})
        return val_macro_f1

    t0 = time.perf_counter()
    run_name = f"{args.model}_{'refit' if args.refit_from else 'search'}"
    with mlflow.start_run(run_name=run_name) as parent_run:
        mlflow.log_params(
            {
                "model": args.model,
                "n_trials": 0 if args.refit_from else args.n_trials,
                "split_strategy": args.split,
                "max_trucks": max_trucks,
                "n_features": len(feat_names),
                "seed": args.seed,
                "refit_from": str(args.refit_from) if args.refit_from else "",
            }
        )
        if args.refit_from:
            informe = json.loads(args.refit_from.read_text(encoding="utf-8"))
            if "best_params" not in informe:
                raise SystemExit(f"{args.refit_from} no trae `best_params`; no hay qué reajustar.")
            study = None
            best_trial_params = informe["best_params"]
            n_trials_previos = informe.get("n_trials")
            search_seconds = 0.0
            print(f"Reajuste desde {args.refit_from} (búsqueda saltada): {best_trial_params}")
        else:
            study = optuna.create_study(
                direction="maximize",
                sampler=optuna.samplers.TPESampler(seed=args.seed),
            )
            study.optimize(objective, n_trials=args.n_trials, n_jobs=args.n_jobs)
            search_seconds = time.perf_counter() - t0
            best_trial_params = study.best_params
            n_trials_previos = args.n_trials

        best_params = finalize_params(args.model, best_trial_params)
        # El ajuste final se hace por tramos para emitir la curva de convergencia.
        # El modelo que sale es el mismo que daría un `.fit()` único --el último
        # tramo tiene todos los árboles o todas las iteraciones--, así que la
        # curva describe exactamente al modelo que se publica.
        print(f"Ajuste final por tramos ({args.model}):")
        best_model, curva, step_unit, pasos = ajustar_con_curva(
            args.model, best_params, train, val, args.seed
        )

        # `predict_proba` sólo devuelve columnas para las clases vistas en
        # `train.target` (`model.classes_`). Si alguna vez faltara una -- p.ej.
        # ningún vehículo fue al camión más chico de una flota de 4 en todo
        # train --, las columnas de `predict_proba` quedarían desalineadas con
        # el índice canónico que espera `decode_episode` (columna `j` = camión
        # `j`). Se falla ruidosamente en vez de decodificar mal en silencio.
        expected_classes = np.arange(n_labels)
        if not np.array_equal(best_model.classes_, expected_classes):
            raise SystemExit(
                f"El mejor modelo sólo vio las clases {best_model.classes_.tolist()} en "
                f"entrenamiento, se esperaban {expected_classes.tolist()}. Revisar el "
                "balance de clases de la partición 'train'."
            )

        policy = select_policy(best_model, episodes["val"], val, n_classes)
        domain = {
            name: domain_metrics_for_split(
                best_model, episodes[name], flat[name], n_classes, policy
            )
            for name in ("train", "val", "test")
        }
        greedy_val = aggregate(evaluate_greedy(episodes["val"], val, n_classes), n_labels)

        mlflow.log_params({"best_" + k: v for k, v in best_trial_params.items()})
        mlflow.log_param("decoder_policy", policy)
        mlflow.log_metrics(
            {
                f"{name}_{metric}": value
                for name, m in domain.items()
                for metric, value in m.items()
                if isinstance(value, (int, float))
            }
        )
        # El binario del modelo NO siempre va a MLflow. El bosque del RF ocupa
        # 1,4 GB --500 árboles de profundidad 26 sobre 444.051 filas-- y
        # serializarlo agotaba la memoria de la máquina: el reajuste del 16 de
        # agosto murió exactamente aquí, y `mlruns/` ya llevaba 1,4 GB de una
        # corrida anterior.
        #
        # Es la misma decisión que el repositorio ya tomó para git (ver
        # `.gitignore`: `artifacts/rf/model.joblib` está excluido por tamaño) y
        # por el mismo motivo: no se pierde nada reproducible, porque
        # `training_report.json` guarda `best_params`, la semilla es fija y
        # `--refit-from` reconstruye el modelo. La regresión logística pesa 1,4 kB
        # y se registra con normalidad.
        if _cabe_en_mlflow(best_model, args.model):
            mlflow.sklearn.log_model(best_model, name="model")
        else:
            mlflow.set_tag("model_artifact", "omitido por tamaño; ver artifacts/<modelo>/")
            print(
                f"MLflow: no se registra el binario de {args.model} (demasiado grande). "
                "Se reconstruye con --refit-from."
            )
        best_run_id = parent_run.info.run_id

    # --- Artefactos ------------------------------------------------------------
    # Los tres JSON terminan en salto de línea: sin él, el hook end-of-file-fixer
    # los reescribe en cada commit posterior a un reentrenamiento.
    import joblib

    joblib.dump(best_model, out_dir / "model.joblib")

    # Curva de convergencia y matriz de confusión, en el formato común a los seis
    # modelos (`src/modeling/figures.py`). Estos dos eran los únicos que no
    # producían ninguna de las dos figuras del póster.
    presentacion = PRESENTACION[args.model]
    write_history(out_dir / "training_history.csv", curva, step_unit, steps=pasos)
    plot_curves(
        curva,
        step_unit,
        out_dir / "learning_curves.png",
        presentacion.titulo,
        steps=pasos,
        metrica=presentacion.metrica,
        nombre_metrica=presentacion.nombre_metrica,
        nota=(
            f"La pérdida de entrenamiento se evalúa sobre una muestra fija de "
            f"{MUESTRA_CURVA:,} filas; la de validación, sobre las "
            f"{len(val.target):,} completas."
        ),
    )
    # Sobre VALIDACIÓN, que es la partición de la tabla comparativa y la única
    # que se puede poner al lado de las figuras de los otros cuatro modelos.
    plot_confusion_matrix(
        domain["val"]["confusion_matrix"],
        etiquetas_canonicas(n_labels),
        presentacion.titulo_matriz,
        out_dir / "confusion_matrix.png",
    )

    (out_dir / "feature_schema.json").write_text(
        json.dumps(
            {
                "model": args.model,
                "classes": classes,
                "max_trucks_padding": max_trucks,
                "feature_names": feat_names,
                "blocks": scaler.to_dict(),
                "decoder_policy": policy,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    (out_dir / "label_mapping.json").write_text(
        json.dumps(
            {
                "0": "SIN_CAMION",
                **{str(i + 1): f"CAMION_{i + 1}" for i in range(max_trucks)},
                "_nota": (
                    "Índices canónicos: CAMION_1 es el camión de MAYOR capacidad del "
                    "episodio. Ver src/modeling/canonicalization.py."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    label_counts = {
        name: {
            str(k): int(v) for k, v in zip(*np.unique(a.target, return_counts=True), strict=True)
        }
        for name, a in flat.items()
    }
    (out_dir / "training_report.json").write_text(
        json.dumps(
            {
                "generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                "model": args.model,
                "episodes_dir": str(args.episodes_dir),
                "split_strategy": args.split,
                "episodes_dropped_non_optimal": n_non_optimal,
                "splits": [s.as_dict() for s in summaries],
                "canonical_label_counts": label_counts,
                "n_trials": n_trials_previos,
                "best_params": best_trial_params,
                # Con --refit-from no hay búsqueda nueva, así que no hay
                # `best_value` que reportar: se arrastra el del informe original
                # para que el JSON siga diciendo de dónde salieron los params.
                "best_val_macro_f1": (
                    study.best_value if study else informe.get("best_val_macro_f1")
                ),
                "refit_from": str(args.refit_from) if args.refit_from else None,
                "curve_step_unit": step_unit,
                "decoder_policy": policy,
                "domain_metrics": domain,
                "greedy_baseline_val": greedy_val,
                "search_seconds": round(search_seconds, 1),
                "mlflow_tracking_uri": args.tracking_uri,
                "mlflow_experiment": experiment_name,
                "mlflow_run_id": best_run_id,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    if study:
        print(f"\nBúsqueda: {args.n_trials} intentos en {search_seconds:.1f}s")
    else:
        print(f"\nSin búsqueda: hiperparámetros reajustados desde {args.refit_from}")
    print(f"Mejores hiperparámetros: {best_trial_params}")
    print(f"Política de decodificador elegida: {policy}")
    print(
        f"Test  -- capacity_violation_rate={domain['test']['capacity_violation_rate']:.4f}  "
        f"loaded_gap_mean={domain['test']['loaded_gap_mean']:.4f}  "
        f"raw_assignment_accuracy={domain['test']['raw_assignment_accuracy']:.4f}"
    )
    print(f"Artefactos en {out_dir}")
    print(f"MLflow: experimento '{experiment_name}', run {best_run_id} en {args.tracking_uri}")


if __name__ == "__main__":
    main()
