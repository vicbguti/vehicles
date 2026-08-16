"""La curva de convergencia de los clásicos describe al modelo publicado.

El Random Forest y la regresión logística no tienen época, así que su curva se
obtiene ajustando por tramos con `warm_start`. Eso sólo es honesto si el modelo
que sale del último tramo es **el mismo** que daría un ajuste único: si no, la
curva describiría a un modelo y la tabla comparativa a otro.

Esa equivalencia no es evidente —`warm_start` reanuda un estado, no lo repite—
y es exactamente el tipo de suposición que conviene fijar en vez de creer.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "train_classical", REPO / "scripts" / "train_classical.py"
)
tc = importlib.util.module_from_spec(_spec)
sys.modules["train_classical"] = tc
_spec.loader.exec_module(tc)


def _datos(n=600, seed=0):
    from sklearn.datasets import make_classification

    X, y = make_classification(
        n_samples=n,
        n_features=12,
        n_informative=8,
        n_classes=5,
        n_clusters_per_class=1,
        random_state=seed,
    )
    corte = int(0.7 * n)
    return (
        SimpleNamespace(X=X[:corte], target=y[:corte]),
        SimpleNamespace(X=X[corte:], target=y[corte:]),
    )


def _params_rf(**extra) -> dict:
    """Los hiperparámetros fijos de producción, con el bosque encogido.

    Incluye `class_weight="balanced"`, que importa: sklearn avisa de que no lo
    recomienda junto a `warm_start` «si los datos ajustados difieren del conjunto
    completo». Aquí nunca difieren --siempre se ajusta el train entero-- así que
    los pesos se recalculan idénticos en cada tramo, pero la prueba tiene que
    correr con la configuración real para que eso quede comprobado y no supuesto.
    """
    return {**tc.fixed_extras("rf"), "n_jobs": 1, **extra}


def test_el_bosque_por_tramos_es_el_mismo_que_de_una_vez():
    """`warm_start` acumula árboles en el mismo bosque, no rehace el bosque.

    Si esto dejara de cumplirse, la curva seguiría dibujándose --y seguiría
    pareciendo razonable-- mientras describe a un modelo distinto del publicado.
    """
    train, val = _datos()
    params = _params_rf(n_estimators=50)

    unico = tc.build_model("rf", params).fit(train.X, train.target)
    por_tramos, _, _, _ = tc.ajustar_con_curva("rf", params, train, val, seed=42)

    assert np.array_equal(unico.predict_proba(val.X), por_tramos.predict_proba(val.X))


def test_el_bosque_grande_no_se_registra_en_mlflow():
    """El bosque publicado ocupa 1,4 GB y serializarlo mató una corrida entera.

    Es la misma decisión que ya está tomada para git (`.gitignore` excluye
    `artifacts/rf/model.joblib`): no se pierde nada reproducible porque
    `best_params` y la semilla bastan para reconstruirlo con `--refit-from`.
    """
    train, _ = _datos()
    chico = tc.build_model("rf", _params_rf(n_estimators=5, max_depth=3)).fit(train.X, train.target)
    assert tc._cabe_en_mlflow(chico, "rf")

    # Se decide contando nodos, no por el nombre del modelo: un bosque chico sí
    # cabe, y un `if model_name == "rf"` lo habría excluido igual.
    tc_max = tc.MAX_NODOS_MLFLOW
    try:
        tc.MAX_NODOS_MLFLOW = 1
        assert not tc._cabe_en_mlflow(chico, "rf")
    finally:
        tc.MAX_NODOS_MLFLOW = tc_max


def test_la_logistica_siempre_se_registra_en_mlflow():
    """Pesa 1,4 kB: el límite existe por el bosque, no por los clásicos."""
    train, _ = _datos()
    modelo = tc.build_model("logreg", {"max_iter": 100, "random_state": 42}).fit(
        train.X, train.target
    )
    assert tc._cabe_en_mlflow(modelo, "logreg")


def test_la_logistica_publicada_es_la_de_un_ajuste_unico():
    """En la logística la curva NO puede salir de reanudar lbfgs.

    Reanudar pierde la aproximación del Hessiano, así que diez tramos de 200
    iteraciones rinden mucho menos que 2.000 seguidas. Medido sobre los datos
    reales del proyecto, los tramos terminaban sin converger y daban un modelo
    **peor** que un ajuste único: log-loss de validación 0,3990 contra 0,3982 y
    coeficientes de norma media 2,34 contra 3,34 --infra-ajustado--. Eso sería
    degradar el modelo publicado a cambio de poder dibujar una figura.

    Por eso cada punto es un ajuste independiente con presupuesto creciente, y el
    último usa el presupuesto completo: el modelo que sale es, por construcción,
    el mismo que daría `fit()` a secas.
    """
    train, val = _datos()
    params = {"max_iter": 400, "random_state": 42, "C": 1.0}

    unico = tc.build_model("logreg", params).fit(train.X, train.target)
    publicado, _, _, _ = tc.ajustar_con_curva("logreg", params, train, val, seed=42)

    assert np.array_equal(unico.coef_, publicado.coef_)
    assert publicado.predict(val.X).tolist() == unico.predict(val.X).tolist()


def test_la_logistica_no_reanuda_entre_presupuestos():
    """Fija la decisión, no sólo su efecto: si alguien volviera a poner
    `warm_start=True` aquí «para ahorrar tiempo», el modelo publicado empeoraría
    en silencio y la prueba de arriba tardaría en delatarlo."""
    train, val = _datos()
    modelo, _, _, _ = tc.ajustar_con_curva(
        "logreg", {"max_iter": 400, "random_state": 42, "C": 1.0}, train, val, seed=42
    )

    assert modelo.get_params()["warm_start"] is False


def test_cada_modelo_declara_su_propio_eje():
    """Rotular «época» cualquiera de las dos sería falso, y son ejes distintos
    entre sí: árboles no es lo mismo que iteraciones del optimizador."""
    train, val = _datos()

    _, _, eje_rf, _ = tc.ajustar_con_curva(
        "rf", {"n_estimators": 20, "random_state": 42, "n_jobs": 1}, train, val, seed=42
    )
    _, _, eje_lr, _ = tc.ajustar_con_curva(
        "logreg", {"max_iter": 100, "random_state": 42, "C": 1.0}, train, val, seed=42
    )

    assert (eje_rf, eje_lr) == ("n_trees", "lbfgs_iter")


def test_la_curva_trae_las_cuatro_series_en_cada_tramo():
    train, val = _datos()
    _, curva, _, _ = tc.ajustar_con_curva(
        "rf", {"n_estimators": 20, "random_state": 42, "n_jobs": 1}, train, val, seed=42
    )

    assert len(curva) >= tc.TRAMOS
    assert set(curva[0]) == {"loss", "val_loss", "macro_f1", "val_macro_f1"}


def test_el_bosque_mejora_conforme_crece():
    """Comprobación de cordura: si la curva saliera plana o al revés, es que los
    tramos no están acumulando nada."""
    train, val = _datos(n=1200)
    _, curva, _, _ = tc.ajustar_con_curva(
        "rf", {"n_estimators": 60, "random_state": 42, "n_jobs": 1}, train, val, seed=42
    )

    assert curva[-1]["val_loss"] < curva[0]["val_loss"]


def test_el_modelo_devuelto_no_arrastra_warm_start():
    """`warm_start` era un medio para dibujar la curva, no una propiedad del
    modelo que se guarda: si quedara puesto, un `fit` posterior añadiría árboles
    a los que ya hay en vez de entrenar de cero."""
    train, val = _datos()
    modelo, _, _, _ = tc.ajustar_con_curva(
        "rf", {"n_estimators": 20, "random_state": 42, "n_jobs": 1}, train, val, seed=42
    )

    assert modelo.get_params()["warm_start"] is False


@pytest.mark.parametrize("modelo", ["rf", "logreg"])
def test_los_tramos_terminan_en_el_presupuesto_completo(modelo):
    """El último tramo tiene todos los árboles o todas las iteraciones; si no,
    el modelo publicado sería más chico que el que declaran sus hiperparámetros."""
    total = 500 if modelo == "rf" else 2000
    params = {"n_estimators": 500} if modelo == "rf" else {"max_iter": 2000}
    _, _clave, tramos = tc._eje_y_tramos(modelo, params)

    # Acumulados y sin repetir el último: reajustar con el mismo presupuesto no
    # añade nada y sklearn lo advierte.
    assert tramos[-1] == total
    assert tramos == sorted(set(tramos))
