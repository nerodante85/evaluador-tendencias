import json
import urllib.error

import pytest

from pipeline.fuentes import wikipedia as wp


class _RespuestaFalsa:
    def __init__(self, cuerpo):
        self._cuerpo = cuerpo
        self.status = 200

    def read(self):
        return self._cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _items(*pares):
    """pares: (aaaammdd_hh, vistas)."""
    return json.dumps({"items": [{"timestamp": ts, "views": v} for ts, v in pares]}).encode("utf-8")


def test_vistas_mensuales_parsea_fecha_y_vistas(monkeypatch):
    monkeypatch.setattr(wp.urllib.request, "urlopen", lambda req, timeout=20: _RespuestaFalsa(_items(("2020010100", 543), ("2020020100", 601))))
    backend = wp.BackendWikipediaPageviews(pausa=0)
    r = backend.vistas_mensuales("Crochet", "2020010100", "2020030100")
    assert r == [{"fecha": "2020-01-01", "vistas": 543}, {"fecha": "2020-02-01", "vistas": 601}]


def test_articulo_inexistente_devuelve_lista_vacia_no_excepcion(monkeypatch):
    def urlopen_falso(req, timeout=20):
        raise urllib.error.HTTPError(req.full_url, 404, "not found", {}, None)

    # HTTPError.read() necesita que el "fp" tenga .read(); se simula abajo
    class _Err404(urllib.error.HTTPError):
        def read(self):
            return b"not found"

    def urlopen_falso(req, timeout=20):
        raise _Err404(req.full_url, 404, "not found", {}, None)

    monkeypatch.setattr(wp.urllib.request, "urlopen", urlopen_falso)
    backend = wp.BackendWikipediaPageviews(pausa=0)
    assert backend.vistas_mensuales("Articulo Que No Existe De Verdad", "2020010100", "2020030100") == []


def test_bloqueo_429_lanza_bloqueado_no_sin_articulo(monkeypatch):
    class _Err429(urllib.error.HTTPError):
        def read(self):
            return b"too many requests"

    def urlopen_falso(req, timeout=20):
        raise _Err429(req.full_url, 429, "too many", {}, None)

    monkeypatch.setattr(wp.urllib.request, "urlopen", urlopen_falso)
    backend = wp.BackendWikipediaPageviews(pausa=0)
    with pytest.raises(wp.Bloqueado):
        backend.vistas_mensuales("Moda", "2020010100", "2020030100")


def test_otro_error_http_no_se_confunde_con_bloqueo_ni_articulo_faltante(monkeypatch):
    class _Err500(urllib.error.HTTPError):
        def read(self):
            return b"server error"

    def urlopen_falso(req, timeout=20):
        raise _Err500(req.full_url, 500, "server error", {}, None)

    monkeypatch.setattr(wp.urllib.request, "urlopen", urlopen_falso)
    backend = wp.BackendWikipediaPageviews(pausa=0)
    with pytest.raises(wp.ErrorFuente):
        backend.vistas_mensuales("Moda", "2020010100", "2020030100")


def test_el_titulo_con_espacios_y_tildes_se_codifica_para_la_url(monkeypatch):
    capturada = {}

    def urlopen_falso(req, timeout=20):
        capturada["url"] = req.full_url
        return _RespuestaFalsa(_items())

    monkeypatch.setattr(wp.urllib.request, "urlopen", urlopen_falso)
    backend = wp.BackendWikipediaPageviews(pausa=0)
    backend.vistas_mensuales("Pantalón cargo", "2020010100", "2020030100")
    assert "Pantal%C3%B3n_cargo" in capturada["url"]


def test_usa_el_proyecto_configurado_en_la_url(monkeypatch):
    capturada = {}

    def urlopen_falso(req, timeout=20):
        capturada["url"] = req.full_url
        return _RespuestaFalsa(_items())

    monkeypatch.setattr(wp.urllib.request, "urlopen", urlopen_falso)
    backend = wp.BackendWikipediaPageviews(proyecto="en.wikipedia", pausa=0)
    backend.vistas_mensuales("Denim", "2020010100", "2020030100")
    assert "/en.wikipedia/" in capturada["url"]
