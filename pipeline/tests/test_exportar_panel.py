from pipeline.exportar_panel import construir_catalogo, construir_metodologia
from pipeline.taxonomia import Mercado, Nodo, Taxonomia


def _tax():
    mercados = {"CO": Mercado("CO", "Colombia", "es-CO", 300), "MX": Mercado("MX", "México", "es-MX", 360)}
    nodos = {
        "prenda.jean": Nodo("prenda.jean", "prenda", "Jean", {"CO": "jean", "MX": "jeans"}, relaciones=("tela.denim",)),
        "prenda.sin_datos": Nodo("prenda.sin_datos", "prenda", "Sin datos", {"CO": "x", "MX": "x"}),
        "color.rojo": Nodo("color.rojo", "color", "Rojo", {"CO": "rojo", "MX": "rojo"}, hex="#C22E22", familia="rojo"),
    }
    return Taxonomia(mercados, nodos, {}, {})


def _serie(n=60, nivel=30):
    fechas = [f"20{4 + i // 12:02d}-{i % 12 + 1:02d}-01" for i in range(n)]
    return {"serie": [[f, nivel] for f in fechas]}


def _leer_serie_falso(clave):
    return _serie()


def _ruta_falsa(mercado, nodo, dir_raw):
    return (mercado, nodo)  # el "leer_serie" de arriba ignora esto


def _construir(tax, calidad, trend_score=None):
    return construir_catalogo(tax, calidad, trend_score, dir_raw=None, leer_serie=_leer_serie_falso, ruta_serie=_ruta_falsa)


def test_los_nodos_sin_ningun_mercado_con_datos_no_entran_al_catalogo():
    tax = _tax()
    calidad = {
        ("CO", "prenda.jean"): {"clase": "apta_backtest"},
        ("MX", "prenda.jean"): {"clase": "apta_senal"},
        ("CO", "prenda.sin_datos"): {"clase": "insuficiente"},
        ("MX", "prenda.sin_datos"): {"clase": "sin_datos"},
        ("CO", "color.rojo"): {"clase": "apta_backtest"},
        ("MX", "color.rojo"): {"clase": "insuficiente"},
    }
    catalogo = _construir(tax, calidad)
    assert "prenda.sin_datos" not in catalogo
    assert set(catalogo["prenda.jean"]["mercados"]) == {"CO", "MX"}
    assert set(catalogo["color.rojo"]["mercados"]) == {"CO"}  # MX quedó afuera (insuficiente)


def test_incluye_metadatos_de_taxonomia_y_relaciones():
    tax = _tax()
    calidad = {("CO", "prenda.jean"): {"clase": "apta_backtest"}, ("MX", "prenda.jean"): {"clase": "sin_datos"}}
    catalogo = _construir(tax, calidad)
    entrada = catalogo["prenda.jean"]
    assert entrada["tipo"] == "prenda"
    assert entrada["relaciones"] == ["tela.denim"]
    assert entrada["mercados"]["CO"]["query"] == "jean"


def test_usa_el_score_calibrado_cuando_existe_y_calcula_estado_actual_de_la_serie():
    tax = _tax()
    calidad = {("CO", "prenda.jean"): {"clase": "apta_backtest"}}
    trend_score = {"señales": {"CO|prenda.jean": {"score": 71.2, "estacional": True, "crecimiento": 0.4, "persistencia": 10, "aceleracion": 0.1, "volatilidad": 0.2, "saturacion": 0.6}}}
    catalogo = _construir(tax, calidad, trend_score)
    m = catalogo["prenda.jean"]["mercados"]["CO"]
    assert m["score_24m"] == 71.2
    assert m["estacional"] is True
    assert m["estado_actual"] == "estable"  # serie plana de la prueba
    assert m["momentum"] == 30.0


def test_sin_score_calibrado_cae_a_lo_que_de_el_motor_de_senales():
    tax = _tax()
    calidad = {("CO", "prenda.jean"): {"clase": "apta_senal"}}
    catalogo = _construir(tax, calidad)
    m = catalogo["prenda.jean"]["mercados"]["CO"]
    assert m["score_24m"] is None
    assert m["estado_actual"] == "estable"


# --- construir_metodologia: tolera archivos faltantes ---


def test_construir_metodologia_sin_archivos_no_revienta():
    m = construir_metodologia(pesos=None, backtesting=None)
    assert m == {"trend_score": None, "backtesting": None}


def test_construir_metodologia_con_datos_los_pasa_tal_cual():
    pesos = {
        "horizonte_meses": 24, "variables": ["crecimiento"], "coeficientes": {"crecimiento": 0.1},
        "n_entrenamiento": 10, "n_prueba": 5, "evaluacion_fuera_de_muestra": {"auc": 0.6}, "calibrado": "2026-09-27T00:00",
        "intervalos_95": {"crecimiento": [-0.1, 0.3]},
    }
    backtesting = {
        "n_series": 10, "n_cortes": 5, "n_filas": 100, "metricas": {}, "veredicto_bonferroni": {},
        "clase_mayoritaria": {"24": 0.4}, "generado": "2026-09-27T00:00",
    }
    m = construir_metodologia(pesos, backtesting)
    assert m["trend_score"]["evaluacion"] == {"auc": 0.6}
    assert m["trend_score"]["intervalos_95"] == {"crecimiento": [-0.1, 0.3]}
    assert m["backtesting"]["clase_mayoritaria"] == {"24": 0.4}


def test_construir_metodologia_sin_intervalos_no_revienta():
    # pesos generados antes de que existiera "intervalos_95" en el JSON —
    # no debe romper el export, solo faltar el campo.
    pesos = {
        "horizonte_meses": 24, "variables": ["crecimiento"], "coeficientes": {"crecimiento": 0.1},
        "n_entrenamiento": 10, "n_prueba": 5, "evaluacion_fuera_de_muestra": {"auc": 0.6}, "calibrado": "2026-09-27T00:00",
    }
    m = construir_metodologia(pesos, backtesting=None)
    assert m["trend_score"]["intervalos_95"] == {}
