import pytest

from pipeline.modelos import MODELOS, holt_winters, media_movil, naive_estacional, sarima


def _serie_estacional(anos=6, base=30, amplitud=15):
    """Sube en diciembre, plana el resto, sin tendencia — para poder
    verificar que un modelo de verdad "aprendió" la estacionalidad."""
    un_ano = [base] * 11 + [base + amplitud]
    return un_ano * anos


# --- naive_estacional ---


def test_naive_repite_el_mismo_mes_del_ano_anterior():
    serie = _serie_estacional(anos=3)
    pron = naive_estacional(serie, 12)
    assert pron == serie[-12:]


def test_naive_repite_el_ciclo_completo_mas_alla_de_12_meses():
    serie = _serie_estacional(anos=3)
    pron = naive_estacional(serie, 24)
    assert pron[:12] == pron[12:24] == serie[-12:]


def test_naive_sin_12_meses_de_historia_repite_el_ultimo_valor():
    assert naive_estacional([5, 8, 9], 4) == [9, 9, 9, 9]


def test_naive_con_serie_vacia_no_revienta():
    assert naive_estacional([], 3) == [0, 0, 0]


# --- media_movil ---


def test_media_movil_es_plana_en_el_promedio_de_la_ventana():
    serie = [10] * 6 + [20] * 6  # promedio de los últimos 12 = 15
    assert media_movil(serie, 5) == [15.0] * 5


def test_media_movil_usa_toda_la_serie_si_es_mas_corta_que_la_ventana():
    assert media_movil([10, 20, 30], 2, ventana=12) == [20.0, 20.0]


# --- holt_winters ---


def test_holt_winters_cae_a_media_movil_con_poca_historia():
    serie = [10] * 20
    assert holt_winters(serie, 3) == media_movil(serie, 3)


def test_holt_winters_aprende_la_estacionalidad():
    serie = _serie_estacional(anos=6, base=30, amplitud=20)
    pron = holt_winters(serie, 12)
    # el mes 12 pronosticado (diciembre) debe quedar claramente por encima
    # de un mes cualquiera de mitad de año — si no, no aprendió el patrón.
    assert pron[11] > pron[5] + 5


def test_holt_winters_nunca_pronostica_negativo():
    serie = [0, 1, 0, 2, 0, 1] * 6
    assert all(v >= 0 for v in holt_winters(serie, 12))


def test_holt_winters_no_se_cuelga_con_serie_totalmente_plana_en_cero():
    # No es un caso hipotético: antes de la guarda de _es_degenerada() esto
    # colgaba el proceso (no lanzaba excepción, se quedaba sin terminar) al
    # intentar diferenciar una serie constante. Series así existen de
    # verdad entre las de bajo volumen.
    assert holt_winters([0] * 40, 6) == [0.0] * 6


def test_holt_winters_no_se_cuelga_con_serie_casi_plana():
    pron = holt_winters([10] * 39 + [11], 6)
    assert len(pron) == 6


# --- sarima ---


def test_sarima_cae_a_media_movil_con_poca_historia():
    serie = [10] * 30
    assert sarima(serie, 3) == media_movil(serie, 3)


def test_sarima_produce_el_largo_pedido_y_no_negativo():
    serie = _serie_estacional(anos=8, base=25, amplitud=15)
    pron = sarima(serie, 12)
    assert len(pron) == 12
    assert all(v >= 0 for v in pron)


def test_sarima_no_se_cuelga_con_serie_degenerada():
    # Igual que Holt-Winters: una serie constante colgaba el ajuste (no
    # lanzaba excepción) antes de la guarda de _es_degenerada().
    assert sarima([5] * 60, 6) == [5.0] * 6


# --- contrato común a los cuatro modelos ---


@pytest.mark.parametrize("nombre", list(MODELOS))
def test_todos_los_modelos_devuelven_el_largo_exacto_pedido(nombre):
    serie = _serie_estacional(anos=5)
    assert len(MODELOS[nombre](serie, 7)) == 7


@pytest.mark.parametrize("nombre", list(MODELOS))
def test_todos_los_modelos_toleran_series_cortas_sin_reventar(nombre):
    for serie in ([], [5], [5, 5, 5]):
        assert len(MODELOS[nombre](serie, 4)) == 4
