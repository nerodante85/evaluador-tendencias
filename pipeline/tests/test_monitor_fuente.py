import pytest

from pipeline.fuentes.trends import Bloqueado, ErrorFuente
from pipeline.monitor_fuente import chequear
from pipeline.taxonomia import Mercado

CO = Mercado("CO", "Colombia", "es-CO", 300)


class _BackendFalso:
    def __init__(self, resultado=None, excepcion=None):
        self._resultado = resultado
        self._excepcion = excepcion

    def interes_en_el_tiempo(self, consulta, mercado, categoria=68, timeframe="today 3-m"):
        if self._excepcion:
            raise self._excepcion
        return self._resultado


def test_datos_reales_es_ok():
    ok, msg = chequear(_BackendFalso(resultado=[{"fecha": "2026-09-01", "valor": 40, "parcial": False}]), mercado=CO)
    assert ok is True
    assert "OK" in msg


def test_bloqueo_no_es_ok_y_lo_dice():
    ok, msg = chequear(_BackendFalso(excepcion=Bloqueado("429")), mercado=CO)
    assert ok is False
    assert "bloqueado" in msg.lower()


def test_error_de_fuente_no_es_ok():
    ok, msg = chequear(_BackendFalso(excepcion=ErrorFuente("500")), mercado=CO)
    assert ok is False


def test_error_inesperado_tambien_cuenta_como_roto():
    ok, msg = chequear(_BackendFalso(excepcion=RuntimeError("algo raro")), mercado=CO)
    assert ok is False
    assert "inesperado" in msg.lower()


def test_respuesta_vacia_sin_error_no_es_ok():
    # pytrends a veces "funciona" (sin excepción) pero no trae nada — para un
    # término tan estable como "jean" eso es igual de sospechoso que un error.
    ok, msg = chequear(_BackendFalso(resultado=[]), mercado=CO)
    assert ok is False
    assert "sin ningún dato" in msg


@pytest.mark.parametrize("resultado", [None, []])
def test_ningun_dato_utilizable_no_es_ok(resultado):
    ok, _ = chequear(_BackendFalso(resultado=resultado), mercado=CO)
    assert ok is False
