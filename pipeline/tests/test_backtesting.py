from pipeline.backtesting import (
    Metricas,
    Resultado,
    agregar_por_modelo_y_horizonte,
    comparar_contra_baseline,
    cortes_de_prueba,
    emparejar_con_baseline,
    evaluar_serie,
    frecuencia_clase_mayoritaria,
    muestra_estratificada,
)
from pipeline.taxonomia import Mercado, Nodo, Taxonomia

# --- cortes_de_prueba: dónde se permite parar a "mirar hacia adelante" ---


def test_cortes_dejan_calentamiento_despues_del_inicio_util():
    # inicio_util=20, calentamiento=36 -> el primer corte válido es 20+36-1=55
    cortes = cortes_de_prueba(n=200, inicio_util=20, n_cortes=3, meses_max=24, calentamiento=36)
    assert cortes[0] == 55


def test_cortes_dejan_margen_para_el_horizonte_mas_largo():
    cortes = cortes_de_prueba(n=200, inicio_util=0, n_cortes=3, meses_max=24, calentamiento=36)
    assert cortes[-1] == 200 - 1 - 24


def test_sin_espacio_suficiente_no_hay_cortes():
    assert cortes_de_prueba(n=40, inicio_util=0, n_cortes=5, meses_max=24, calentamiento=36) == []


def test_un_solo_corte_pedido_da_el_ultimo_valido():
    cortes = cortes_de_prueba(n=200, inicio_util=0, n_cortes=1, meses_max=24, calentamiento=36)
    assert cortes == [200 - 1 - 24]


def test_los_cortes_quedan_espaciados_y_sin_repetidos():
    cortes = cortes_de_prueba(n=300, inicio_util=0, n_cortes=6, meses_max=24, calentamiento=36)
    assert len(cortes) == len(set(cortes))
    assert cortes == sorted(cortes)
    assert len(cortes) == 6


def test_inicio_util_none_se_trata_como_cero():
    a = cortes_de_prueba(n=200, inicio_util=None, n_cortes=3, meses_max=24, calentamiento=36)
    b = cortes_de_prueba(n=200, inicio_util=0, n_cortes=3, meses_max=24, calentamiento=36)
    assert a == b


# --- evaluar_serie: el mecanismo central ---


def _serie_alza_clara(antes=48, nivel_bajo=15, nivel_alto=45, cola=48):
    return [nivel_bajo] * antes + [nivel_alto] * cola


def test_evaluar_serie_produce_una_fila_por_corte_modelo_y_horizonte():
    serie = _serie_alza_clara()
    cortes = [60, 70]
    modelos = {"naive_estacional": lambda v, m: [v[-1]] * m}
    filas = evaluar_serie(serie, cortes, modelos=modelos, horizontes=(6, 12))
    assert len(filas) == len(cortes) * len(modelos) * 2
    claves = {(f.corte, f.modelo, f.horizonte) for f in filas}
    assert claves == {(60, "naive_estacional", 6), (60, "naive_estacional", 12), (70, "naive_estacional", 6), (70, "naive_estacional", 12)}


def test_un_modelo_perfecto_acierta_siempre_en_una_serie_de_manual():
    # "perfecto" = adivina exactamente lo que la serie real trae después
    def oraculo(conocida, meses):
        corte = len(conocida) - 1
        return serie[corte + 1 : corte + 1 + meses]

    serie = _serie_alza_clara(antes=48, cola=48)
    modelos = {"oraculo": oraculo}
    filas = evaluar_serie(serie, cortes=[55, 65], modelos=modelos, horizontes=(6, 12, 24))
    assert all(f.acierto for f in filas)
    assert all(f.error_futuro == 0 for f in filas)


def test_un_modelo_que_siempre_falla_el_pronostico_no_acierta_una_alza():
    def pesimo(conocida, meses):
        return [0] * meses  # siempre predice "nada de interés"

    serie = _serie_alza_clara()
    filas = evaluar_serie(serie, cortes=[60], modelos={"pesimo": pesimo}, horizontes=(12,))
    assert filas[0].etiqueta_pred != filas[0].etiqueta_real


def test_un_modelo_que_revienta_no_tumba_el_backtesting_completo():
    def revienta(conocida, meses):
        raise ValueError("no converge")

    serie = _serie_alza_clara()
    filas = evaluar_serie(serie, cortes=[60], modelos={"malo": revienta}, horizontes=(12,))
    assert len(filas) == 1  # cayó a media_movil en vez de propagar la excepción


# --- muestra_estratificada ---


def _tax_con_tipos(conteos):
    """conteos: {"prenda": 5, "color": 5, ...} -> nodos con ese tipo, con 3
    mercados cada uno."""
    mercados = {c: Mercado(c, c, "es", 0) for c in ("CO", "MX", "ES")}
    nodos = {}
    for tipo, n in conteos.items():
        for i in range(n):
            nid = f"{tipo}.n{i}"
            nodos[nid] = Nodo(nid, tipo, nid, {c: nid for c in mercados})
    return Taxonomia(mercados, nodos, {}, {})


def test_la_muestra_reparte_entre_tipos_en_vez_de_solo_tomar_el_mas_grande():
    tax = _tax_con_tipos({"prenda": 30, "color": 30, "estilo": 30})
    calidad = {(c, n): {"clase": "apta_backtest"} for c in tax.mercados for n in tax.nodos}
    m = muestra_estratificada(tax, calidad, n=9)
    tipos = [nid.split(".")[0] for _, nid in m]
    assert tipos.count("prenda") == tipos.count("color") == tipos.count("estilo") == 3


def test_la_muestra_respeta_la_clase_de_calidad():
    tax = _tax_con_tipos({"prenda": 4})
    calidad = {(c, n): {"clase": "insuficiente"} for c in tax.mercados for n in tax.nodos}
    calidad[("CO", "prenda.n0")] = {"clase": "apta_backtest"}
    m = muestra_estratificada(tax, calidad, n=10)
    assert m == [("CO", "prenda.n0")]


def test_la_muestra_es_reproducible_con_la_misma_semilla():
    tax = _tax_con_tipos({"prenda": 20, "color": 20})
    calidad = {(c, n): {"clase": "apta_backtest"} for c in tax.mercados for n in tax.nodos}
    a = muestra_estratificada(tax, calidad, n=8, semilla=7)
    b = muestra_estratificada(tax, calidad, n=8, semilla=7)
    assert a == b


# --- agregación y comparación contra el baseline ---


def _r(modelo, horizonte, acierto, error=1.0):
    # `error` se aplica siempre, acierte o no la etiqueta: son dos preguntas
    # independientes (¿la etiqueta coincidió? ¿qué tan lejos quedó el nivel
    # pronosticado?) y las pruebas que combinan ambas necesitan controlarlas
    # por separado.
    return Resultado("CO", "x", 0, horizonte, modelo, "estable", "estable" if acierto else "alza_sostenida", 10.0, 10.0 + error)


def test_metricas_calcula_exactitud_y_error_mediano():
    m = Metricas()
    for r in [_r("x", 12, True, 0), _r("x", 12, False, 2), _r("x", 12, True, 0), _r("x", 12, False, 4)]:
        m.n += 1
        m.aciertos += int(r.acierto)
        m.errores.append(r.error_futuro)
    assert m.exactitud == 0.5
    assert m.error_mediano == 1.0  # mediana de [0, 2, 0, 4] = 1.0


def test_agregar_separa_por_modelo_y_horizonte():
    resultados = [_r("naive_estacional", 12, True), _r("naive_estacional", 24, False), _r("sarima", 12, True)]
    agg = agregar_por_modelo_y_horizonte(resultados)
    assert set(agg) == {("naive_estacional", 12), ("naive_estacional", 24), ("sarima", 12)}
    assert agg[("naive_estacional", 12)].n == 1


def _par(modelo, horizonte, corte, acierto_base, acierto_modelo):
    """Una fila del baseline y una del modelo para el MISMO caso (mismo
    corte): es lo que emparejar_con_baseline() necesita para comparar como
    corresponde, caso contra caso, no promedio contra promedio."""
    return [
        Resultado("CO", "x", corte, horizonte, "naive_estacional", "estable", "estable" if acierto_base else "alza_sostenida", 10.0, 10.0),
        Resultado("CO", "x", corte, horizonte, modelo, "estable", "estable" if acierto_modelo else "alza_sostenida", 10.0, 10.0),
    ]


def test_un_modelo_que_acierta_donde_el_baseline_falla_casi_siempre_le_gana():
    resultados = []
    for i in range(15):
        resultados += _par("sarima", 12, i, acierto_base=False, acierto_modelo=True)  # discordante a favor del modelo
    for i in range(15, 20):
        resultados += _par("sarima", 12, i, acierto_base=True, acierto_modelo=True)  # concordante, no aporta a la significancia
    veredicto = comparar_contra_baseline(resultados, horizontes=(12,), modelos={"naive_estacional": None, "sarima": None})
    assert veredicto[("sarima", 12)] is True


def test_una_ventaja_de_un_solo_acierto_sobre_muchos_casos_no_es_significativa():
    # El caso real que motivó este test: en la primera corrida del
    # backtesting, sarima salió con 105/172 contra 104/172 del baseline a
    # 12 meses — un solo acierto de diferencia. La comparación anterior
    # (¿es mayor?) lo marcaba como "le gana"; no debería.
    resultados = []
    for i in range(103):
        resultados += _par("sarima", 12, i, acierto_base=True, acierto_modelo=True)
    resultados += _par("sarima", 12, 103, acierto_base=False, acierto_modelo=True)  # el único acierto de más
    for i in range(104, 172):
        resultados += _par("sarima", 12, i, acierto_base=False, acierto_modelo=False)
    veredicto = comparar_contra_baseline(resultados, horizontes=(12,), modelos={"naive_estacional": None, "sarima": None})
    assert veredicto[("sarima", 12)] is False


def test_un_modelo_igual_de_bueno_no_le_gana_al_baseline():
    resultados = []
    for i in range(10):
        resultados += _par("sarima", 12, i, acierto_base=True, acierto_modelo=True)
    veredicto = comparar_contra_baseline(resultados, horizontes=(12,), modelos={"naive_estacional": None, "sarima": None})
    assert veredicto[("sarima", 12)] is False  # sin discordancias no hay nada que le gane a nadie


def test_emparejar_con_baseline_solo_junta_el_mismo_caso():
    resultados = _par("sarima", 12, corte=5, acierto_base=True, acierto_modelo=False) + _par("holt_winters", 12, corte=7, acierto_base=False, acierto_modelo=True)
    pares = emparejar_con_baseline(resultados)
    assert pares[("sarima", 12)] == [(True, False)]
    assert pares[("holt_winters", 12)] == [(False, True)]


def test_sin_casos_emparejados_para_un_modelo_no_hay_veredicto():
    resultados = _par("sarima", 12, 0, True, True)
    veredicto = comparar_contra_baseline(resultados, horizontes=(6,), modelos={"naive_estacional": None, "sarima": None})
    assert ("sarima", 6) not in veredicto


# --- frecuencia_clase_mayoritaria: la vara mínima real, no 25% al azar ---


def _resultado_real(mercado, nodo, corte, horizonte, etiqueta_real):
    return Resultado(mercado, nodo, corte, horizonte, "cualquiera", etiqueta_real, etiqueta_real, 10.0, 10.0)


def test_frecuencia_clase_mayoritaria_con_clases_desbalanceadas():
    # 3 "estable" y 1 "alza_sostenida" -> la mayoritaria pesa 75%, no 25%
    resultados = [
        _resultado_real("CO", "x", 0, 12, "estable"),
        _resultado_real("CO", "x", 1, 12, "estable"),
        _resultado_real("CO", "x", 2, 12, "estable"),
        _resultado_real("CO", "x", 3, 12, "alza_sostenida"),
    ]
    assert frecuencia_clase_mayoritaria(resultados, horizontes=(12,))[12] == 0.75


def test_frecuencia_clase_mayoritaria_no_cuenta_el_mismo_caso_dos_veces_por_modelo():
    # el mismo (mercado, nodo, corte) evaluado por 3 modelos distintos debe
    # contar una sola vez para esta cuenta — la etiqueta real no cambia
    # porque cambie el modelo.
    resultados = [Resultado("CO", "x", 0, 12, m, "estable", "estable", 10.0, 10.0) for m in ("naive_estacional", "sarima", "holt_winters")]
    resultados.append(Resultado("CO", "y", 0, 12, "naive_estacional", "alza_sostenida", "alza_sostenida", 10.0, 10.0))
    assert frecuencia_clase_mayoritaria(resultados, horizontes=(12,))[12] == 0.5  # 1 caso "estable", 1 caso "alza", no 3 contra 1


def test_frecuencia_clase_mayoritaria_por_horizonte_separado():
    resultados = [
        _resultado_real("CO", "x", 0, 6, "estable"),
        _resultado_real("CO", "x", 1, 6, "estable"),
        _resultado_real("CO", "x", 0, 24, "estable"),
        _resultado_real("CO", "x", 1, 24, "alza_sostenida"),
    ]
    freq = frecuencia_clase_mayoritaria(resultados, horizontes=(6, 24))
    assert freq[6] == 1.0
    assert freq[24] == 0.5
