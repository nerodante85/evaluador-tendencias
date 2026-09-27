import json

from pipeline.calidad import evaluar as evaluar_calidad
from pipeline.taxonomia import Mercado, Nodo, Taxonomia
from pipeline.trend_score import (
    Fila,
    Pesos,
    calcular_score,
    construir_dataset,
    dividir_train_test,
    evaluar,
    extraer_features,
)

# --- extraer_features: reusa senales.py truncando la serie ---


def test_extraer_features_solo_usa_datos_hasta_el_corte():
    # Si extraer_features mirara más allá del corte, el crecimiento cambiaría
    # al agregar un año de datos futuros muy distintos.
    serie = [10] * 40 + [100] * 40  # sube fuerte después del índice 39
    fechas = [f"20{10 + i // 12:02d}-{i % 12 + 1:02d}-01" for i in range(len(serie))]
    f_antes = extraer_features(fechas, serie, corte=39)
    assert f_antes["crecimiento"] == 0.0  # todo plano hasta ahí, nada que ver con la subida futura


def test_extraer_features_devuelve_las_cinco_variables_del_score():
    serie = [10 + (i % 5) for i in range(60)]
    fechas = [f"20{10 + i // 12:02d}-{i % 12 + 1:02d}-01" for i in range(len(serie))]
    f = extraer_features(fechas, serie, corte=59)
    assert set(f) >= {"crecimiento", "aceleracion", "persistencia", "volatilidad", "saturacion", "estacional"}


# --- construir_dataset: contra dobles, sin tocar disco ---


def _tax_una_serie():
    mercados = {"CO": Mercado("CO", "Colombia", "es-CO", 300)}
    nodo = Nodo("prenda.n0", "prenda", "N0", {"CO": "n0"})
    return Taxonomia(mercados, {nodo.id: nodo}, {}, {})


def _serie_alza(antes=60, bajo=15, alto=45, cola=60):
    return [bajo] * antes + [alto] * cola


def _fechas(n):
    return [f"20{4 + i // 12:02d}-{i % 12 + 1:02d}-01" for i in range(n)]


def test_construir_dataset_marca_alza_cuando_la_serie_real_termino_en_alza(tmp_path):
    tax = _tax_una_serie()
    calidad = {("CO", "prenda.n0"): {"clase": "apta_backtest"}}

    valores = _serie_alza()
    fechas = _fechas(len(valores))

    def leer_serie_falso(ruta):
        return {"serie": list(zip(fechas, valores))}

    def ruta_falsa(mercado, nodo, dir_raw):
        return (mercado, nodo)  # el "leer_serie" de arriba ignora esto

    filas = construir_dataset(tax, calidad, None, leer_serie_falso, ruta_falsa, n_series=1, n_cortes=4, horizonte=24, log=None)
    assert filas  # al menos un corte cayó en zona evaluable
    assert all(isinstance(f, Fila) for f in filas)
    # el corte más cercano al final del tramo bajo, con el futuro ya en el tramo alto, debe marcar alza
    assert any(f.alza for f in filas)


def test_construir_dataset_descarta_filas_con_features_incompletas(tmp_path):
    tax = _tax_una_serie()
    calidad = {("CO", "prenda.n0"): {"clase": "apta_backtest"}}
    valores = [30] * 50  # corta: no alcanza para volatilidad/aceleración en cortes tempranos, pero es plana (no debería fallar por eso)
    fechas = _fechas(len(valores))

    def leer_serie_falso(ruta):
        return {"serie": list(zip(fechas, valores))}

    filas = construir_dataset(tax, calidad, None, leer_serie_falso, lambda m, n, d: (m, n), n_series=1, n_cortes=3, horizonte=24, log=None)
    # con solo 50 meses no hay margen para horizonte=24 con calentamiento de 36 -> ninguna fila, y no debe reventar
    assert filas == []


# --- dividir_train_test: sin fuga entre series ---


def _fila(mercado, nodo, corte, alza=True):
    return Fila(mercado, nodo, corte, {"crecimiento": 0.1, "aceleracion": 0.0, "persistencia": 6, "volatilidad": 0.3, "saturacion": 0.5}, False, alza)


def test_dividir_train_test_ninguna_serie_queda_en_los_dos_lados():
    filas = [_fila("CO", f"n{i}", c) for i in range(20) for c in (10, 20, 30)]
    train, test = dividir_train_test(filas, frac_train=0.7, semilla=1)
    series_train = {(f.mercado, f.nodo) for f in train}
    series_test = {(f.mercado, f.nodo) for f in test}
    assert series_train.isdisjoint(series_test)
    assert len(train) + len(test) == len(filas)


def test_dividir_train_test_es_reproducible():
    filas = [_fila("CO", f"n{i}", 0) for i in range(10)]
    a = dividir_train_test(filas, semilla=7)
    b = dividir_train_test(filas, semilla=7)
    assert a == b


# --- calcular_score: con pesos conocidos, sin ajustar nada ---


def _pesos_simples():
    # un peso positivo claro en "crecimiento", el resto en cero: el score
    # debe subir cuando crecimiento sube, y nada más debe moverlo.
    variables_ = ("crecimiento", "aceleracion", "persistencia", "volatilidad", "saturacion")
    medias = {v: 0.0 for v in variables_}
    desvios = {v: 1.0 for v in variables_}
    coeficientes = {"crecimiento": 2.0, "aceleracion": 0.0, "persistencia": 0.0, "volatilidad": 0.0, "saturacion": 0.0}
    return Pesos(variables_, coeficientes, intercepto=0.0, medias=medias, desvios=desvios)


def test_calcular_score_sube_con_la_variable_de_peso_positivo():
    pesos = _pesos_simples()
    base = {"crecimiento": 0.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}
    alto = {**base, "crecimiento": 3.0}
    assert calcular_score(alto, pesos) > calcular_score(base, pesos)


def test_calcular_score_ignora_variables_con_peso_cero():
    pesos = _pesos_simples()
    base = {"crecimiento": 1.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}
    otra_volatilidad = {**base, "volatilidad": 5.0}
    assert calcular_score(base, pesos) == calcular_score(otra_volatilidad, pesos)


def test_calcular_score_queda_entre_0_y_100():
    pesos = _pesos_simples()
    extremo = {"crecimiento": 1000.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}
    assert 0.0 <= calcular_score(extremo, pesos) <= 100.0


def test_calcular_score_da_50_en_el_punto_neutro():
    pesos = _pesos_simples()
    neutro = {"crecimiento": 0.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}
    assert calcular_score(neutro, pesos) == 50.0


# --- evaluar: exactitud, referencia de mayoría, AUC ---


def test_evaluar_con_un_score_perfecto_da_auc_1():
    pesos = _pesos_simples()
    filas = [
        Fila("CO", "a", 0, {"crecimiento": 5.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}, False, True),
        Fila("CO", "b", 0, {"crecimiento": -5.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}, False, False),
    ]
    e = evaluar(filas, pesos)
    assert e.auc == 1.0
    assert e.exactitud == 1.0


def test_evaluar_con_scores_invertidos_da_auc_0():
    pesos = _pesos_simples()
    filas = [
        Fila("CO", "a", 0, {"crecimiento": -5.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}, False, True),
        Fila("CO", "b", 0, {"crecimiento": 5.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}, False, False),
    ]
    assert evaluar(filas, pesos).auc == 0.0


def test_evaluar_reporta_la_referencia_de_mayoria():
    pesos = _pesos_simples()
    base = {"crecimiento": 0.0, "aceleracion": 0, "persistencia": 0, "volatilidad": 0, "saturacion": 0}
    filas = [Fila("CO", f"n{i}", 0, base, False, i < 3) for i in range(4)]  # 3 True, 1 False
    assert evaluar(filas, pesos).exactitud_mayoria == 0.75


def test_evaluar_sin_filas_no_revienta():
    e = evaluar([], _pesos_simples())
    assert e.n == 0 and e.auc is None
