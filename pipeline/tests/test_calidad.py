import json
from datetime import date

from pipeline.calidad import clasificar, escribir_informe, evaluar, metricas
from pipeline.historia import ruta_serie
from pipeline.taxonomia import Mercado, Nodo, Taxonomia


def _serie_estable(meses=270, nivel=30):
    return [nivel] * meses


def test_serie_larga_y_con_volumen_sirve_para_backtest():
    m = metricas(_serie_estable())
    assert clasificar(m) == "apta_backtest"


def test_serie_corta_solo_sirve_para_leer_la_senal():
    m = metricas(_serie_estable(meses=60))
    assert m["meses_utiles"] == 60
    assert clasificar(m) == "apta_senal"


def test_serie_que_empieza_tarde_no_cuenta_los_meses_de_ruido_como_historia():
    # 200 meses casi en cero (ruido) y 70 meses con volumen real
    serie = [0, 1, 0, 2] * 50 + [30] * 70
    m = metricas(serie)
    assert 60 <= m["meses_utiles"] <= 75
    assert clasificar(m) == "apta_senal"  # no llega a 120 meses útiles


def test_serie_de_muy_bajo_volumen_es_insuficiente():
    assert clasificar(metricas([1, 0, 2, 0] * 60)) == "insuficiente"


def test_muchos_meses_en_cero_recientes_la_descalifican_del_backtest():
    serie = [30] * 200 + [0] * 20 + [30] * 50  # 20 ceros dentro de los últimos 60 (33 %)
    m = metricas(serie)
    assert m["ceros60"] > 0.10
    assert clasificar(m) != "apta_backtest"


def test_serie_vacia_es_sin_datos():
    assert clasificar(metricas([])) == "sin_datos"


# --- evaluar / informe sobre archivos ---


def _tax():
    ms = {c: Mercado(c, c, "es", 0) for c in ("CO", "MX")}
    nodos = {
        "prenda.a": Nodo("prenda.a", "prenda", "A", {"CO": "a", "MX": "a"}),
        "prenda.b": Nodo("prenda.b", "prenda", "B", {"CO": "b", "MX": "b"}),
    }
    return Taxonomia(ms, nodos, {}, {"estable": ["prenda.a"]})


def _guardar(tmp, mercado, nodo, valores, estado="ok"):
    ruta = ruta_serie(mercado, nodo, tmp)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fechas = [f"{2004 + i // 12}-{i % 12 + 1:02d}-01" for i in range(len(valores))]
    ruta.write_text(json.dumps({"estado": estado, "serie": [[f, v] for f, v in zip(fechas, valores)]}), encoding="utf-8")


def test_evaluar_distingue_no_descargada_de_sin_datos(tmp_path):
    tax = _tax()
    _guardar(tmp_path, "CO", "prenda.a", _serie_estable())
    _guardar(tmp_path, "CO", "prenda.b", [], estado="sin_datos")
    r = evaluar(tax, tmp_path)
    assert r[("CO", "prenda.a")]["clase"] == "apta_backtest"
    assert r[("CO", "prenda.b")]["estado"] == "sin_datos"
    assert r[("MX", "prenda.a")]["estado"] == "no_descargada"
    assert r[("MX", "prenda.a")]["clase"] == "sin_datos"


def test_el_informe_se_escribe_con_conteos_y_control(tmp_path):
    tax = _tax()
    _guardar(tmp_path, "CO", "prenda.a", _serie_estable())
    r = evaluar(tax, tmp_path)
    md, js = tmp_path / "informe.md", tmp_path / "calidad.json"
    escribir_informe(tax, r, md, js, hoy=date(2026, 9, 26))
    texto = md.read_text(encoding="utf-8")
    assert "Nodos en la taxonomía: **2**" in texto
    assert "## Casos de control" in texto and "`prenda.a`" in texto
    assert "| CO | 1 | 0 | 0 | 1 |" in texto  # a: apta_backtest; b: sin_datos
    datos = json.loads(js.read_text(encoding="utf-8"))
    assert datos["series"]["CO|prenda.a"]["clase"] == "apta_backtest"
