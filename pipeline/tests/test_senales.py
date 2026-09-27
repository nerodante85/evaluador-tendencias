from pipeline.senales import (
    aceleracion,
    es_estacional,
    estado_actual,
    etiquetar,
    saturacion,
    variables,
    volatilidad,
)

# --- helpers para construir series sintéticas de comportamiento conocido ---


def _fechas(n, inicio_ano=2004, inicio_mes=1):
    fechas = []
    a, m = inicio_ano, inicio_mes
    for _ in range(n):
        fechas.append(f"{a}-{m:02d}-01")
        m += 1
        if m == 13:
            m = 1
            a += 1
    return fechas


def _plana(n, nivel=30):
    return [nivel] * n


def _rampa(meses_planos, meses_subida, desde=10, hasta=60):
    """Plana en `desde` durante `meses_planos` y sube linealmente hasta
    `hasta` en `meses_subida`, terminando la serie justo ahí (la subida
    todavía reciente, no una meseta vieja): con `estado_actual` (últimos 12
    meses vs. los 12 anteriores) esto cae en plena subida, no después de
    que ya se aplanó."""
    paso = (hasta - desde) / meses_subida
    return [desde] * meses_planos + [round(desde + paso * i) for i in range(1, meses_subida + 1)]


# --- etiquetar(): la regla central ---


def test_alza_sostenida_cuando_el_futuro_crece_persiste_y_no_es_solo_la_mediana():
    serie = [20] * 12 + [30] * 12  # +50%, persistente, mediana también sube
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta == "alza_sostenida"
    assert e.base == 20 and e.futuro == 30
    assert e.crecimiento == 0.5
    assert e.persistencia_alza == 12


def test_baja_sostenida_cuando_el_futuro_cae_y_persiste():
    serie = [40] * 12 + [10] * 12  # -75%
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta == "baja_sostenida"
    assert e.persistencia_baja == 12


def test_pico_de_atencion_un_repunte_que_sube_y_se_apaga_dentro_de_la_ventana():
    # Tres meses cerca de la base, tres meses de furor, y una caída por
    # debajo de la base que dura el resto de la ventana: el promedio y el
    # máximo se disparan, pero no se sostiene.
    futuro = [10, 10, 10, 200, 180, 150, 4, 4, 4, 4, 4, 4]
    serie = [10] * 12 + futuro
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta == "pico_atencion"
    assert e.persistencia_alza < 9  # no llega al umbral de persistencia


def test_estable_cuando_no_pasa_nada():
    serie = [30] * 24
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta == "estable"
    assert e.crecimiento == 0.0


def test_no_evaluable_cuando_todo_esta_bajo_el_piso_de_ruido():
    serie = [1, 2, 0, 1] * 6
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta == "no_evaluable"


def test_sin_ventana_si_falta_historia_para_el_corte():
    serie = [30] * 10  # muy corta
    assert etiquetar(serie, corte=5, horizonte=12).etiqueta == "sin_ventana"
    assert etiquetar(serie, corte=100, horizonte=12).etiqueta == "sin_ventana"


def test_el_piso_de_ruido_evita_crecimientos_absurdos_desde_casi_cero():
    serie = [0] * 12 + [10] * 12  # de 0 a 10: sin piso sería "infinito"
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.base == 0
    assert e.crecimiento == 10 / 5 - 1  # base' = piso de ruido (5), no 0


def test_una_alza_que_no_sostiene_la_mediana_no_es_alza_sostenida():
    # crece +25% en promedio, pero a punta de un solo mes alto: la mediana
    # del futuro se queda cerca de la base, así que no debe calificar.
    serie = [20] * 12 + [20] * 11 + [80]
    e = etiquetar(serie, corte=11, horizonte=12)
    assert e.etiqueta != "alza_sostenida"


# --- estado_actual(): el corte fijo en "hoy" ---


def test_estado_actual_usa_los_ultimos_12_meses_como_futuro():
    serie = list(range(100))  # valores únicos para verificar el corte exacto
    e = estado_actual(serie, horizonte=12)
    assert e.futuro == sum(range(88, 100)) / 12
    assert e.base == sum(range(76, 88)) / 12


# --- aceleración ---


def test_aceleracion_positiva_cuando_el_crecimiento_reciente_es_mayor():
    # crecía +10% hace un año, ahora crece +50%: se está acelerando
    serie = [20] * 12 + [22] * 12 + [30] * 12
    a = aceleracion(serie, horizonte=12)
    assert a is not None and a > 0


def test_aceleracion_negativa_cuando_el_crecimiento_se_frena():
    serie = [20] * 12 + [30] * 12 + [31] * 12  # +50% y luego casi nada más
    a = aceleracion(serie, horizonte=12)
    assert a is not None and a < 0


def test_aceleracion_none_sin_historia_suficiente():
    assert aceleracion([30] * 20, horizonte=12) is None


# --- volatilidad ---


def test_volatilidad_baja_en_serie_estable():
    assert volatilidad([30] * 24) == 0.0


def test_volatilidad_alta_en_serie_erratica():
    assert volatilidad(([0, 40] * 12)) > 0.6


def test_volatilidad_none_si_no_hay_suficientes_datos_o_media_cero():
    assert volatilidad([30]) is None
    assert volatilidad([0, 0, 0]) is None


# --- saturación ---


def test_saturacion_cerca_de_1_en_el_maximo_historico():
    serie = [10] * 100 + [100] * 12  # el nivel actual ES el máximo histórico
    assert saturacion(serie) == 1.0


def test_saturacion_baja_lejos_del_maximo_historico():
    serie = [100] * 12 + [10] * 100  # el pico quedó muy atrás
    assert saturacion(serie) < 0.2


def test_saturacion_none_si_la_serie_nunca_tuvo_volumen():
    assert saturacion([0] * 20) is None


# --- estacionalidad ---


def test_detecta_pico_estacional_que_se_repite_el_mismo_mes():
    fechas = _fechas(36)
    # pico cada diciembre (mes 12), plano el resto, sin crecimiento interanual
    valores = [(50 if (i % 12) == 11 else 10) for i in range(36)]
    assert es_estacional(fechas, valores) is True


def test_no_marca_estacional_una_serie_que_solo_crece():
    fechas = _fechas(36)
    valores = list(range(10, 46))  # crecimiento sostenido, no calendario
    assert es_estacional(fechas, valores) is False


def test_no_marca_estacional_si_el_mes_del_pico_cambia():
    fechas = _fechas(24)
    valores = [10] * 24
    valores[3] = 50  # pico en abril del año 1
    valores[20] = 50  # pico en septiembre del año 2 (mes distinto)
    assert es_estacional(fechas, valores) is False


def test_estacional_none_si_la_serie_es_muy_corta():
    assert es_estacional(_fechas(12), [10] * 12) is None


# --- casos de control, con series sintéticas que imitan el comportamiento
#     real que se espera de cada tipo (no son las series reales de Trends,
#     esas se verifican aparte contra los datos descargados) ---


def test_control_alza_sostenida_estilo_pantalon_cargo():
    serie = _rampa(meses_planos=60, meses_subida=24, desde=8, hasta=40)
    assert estado_actual(serie).etiqueta == "alza_sostenida"


def test_control_pico_estilo_moda_pasajera():
    serie = [15] * 48 + [90] * 3 + [12] * 9  # tres meses de furor y se apaga
    assert estado_actual(serie).etiqueta in ("pico_atencion", "estable")
    # nunca debería leerse como una tendencia sostenida
    assert estado_actual(serie).etiqueta != "alza_sostenida"


def test_control_estable_prenda_basica():
    serie = [40 + (i % 3) for i in range(60)]  # ruido chico alrededor de 40
    assert estado_actual(serie).etiqueta == "estable"


def test_un_auge_que_dura_meses_se_lee_como_alza_mientras_pasa_y_como_baja_despues():
    # Documenta el hallazgo de docs/v2/hallazgo-pico-vs-tendencia.md con una
    # serie sintética: un auge de 16 meses (como el de tie dye en 2020, no
    # un pico de tres semanas) que después colapsa y se queda muerto por
    # años. Mientras dura, es indistinguible de una tendencia real — solo en
    # retrospectiva, con la caída ya ocurrida, se lee como lo que fue.
    antes, auge, despues = 24, 16, 60
    serie = [10] * antes + [90] * auge + [3] * despues

    # Corte con la ventana futura entera todavía dentro del auge (empieza en
    # `antes`=24; con horizonte=12 y ventana=12, cualquier corte entre 23 y
    # antes+auge-12-1=27 deja el futuro completo adentro).
    e_durante = etiquetar(serie, corte=antes + 1, horizonte=12)
    # Justo después de que el auge terminó: la base todavía lo recuerda
    # (ventana base = el final del auge), el futuro ya muestra el colapso.
    e_despues = etiquetar(serie, corte=antes + auge - 1, horizonte=12)

    assert e_durante.etiqueta == "alza_sostenida"
    assert e_despues.etiqueta == "baja_sostenida"
