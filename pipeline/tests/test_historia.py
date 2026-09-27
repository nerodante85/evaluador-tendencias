import json
from datetime import datetime

from pipeline.fuentes.trends import Bloqueado, ErrorFuente
from pipeline.historia import descargar_historia, leer_serie, ruta_serie
from pipeline.taxonomia import Mercado, Nodo, Taxonomia

AHORA = lambda: datetime(2026, 9, 26, 12, 0)


def _tax(n_nodos=3, mercados=("CO", "MX")):
    ms = {c: Mercado(c, c, f"es-{c}", 0) for c in mercados}
    nodos = {}
    for i in range(n_nodos):
        n = Nodo(f"prenda.n{i}", "prenda", f"N{i}", {c: f"q{i}" for c in mercados})
        nodos[n.id] = n
    return Taxonomia(ms, nodos, {}, {})


class Falso:
    """Backend de mentira. `guion` puede traer excepciones que se lanzan en orden."""

    nombre = "falso"

    def __init__(self, filas=None, guion=None):
        self.filas = filas if filas is not None else [
            {"fecha": "2026-07-01", "valor": 40, "parcial": False},
            {"fecha": "2026-08-01", "valor": 44, "parcial": False},
            {"fecha": "2026-09-01", "valor": 52, "parcial": True},
        ]
        self.guion = list(guion or [])
        self.llamadas = []

    def interes_en_el_tiempo(self, consulta, mercado, *a, **k):
        self.llamadas.append((mercado.codigo, consulta))
        if self.guion:
            paso = self.guion.pop(0)
            if isinstance(paso, Exception):
                raise paso
        return self.filas


def _correr(tax, backend, tmp_path, **k):
    esperas = []
    k.setdefault("pausa", 0)
    k.setdefault("jitter", 0)
    r = descargar_historia(tax, backend, dir_raw=tmp_path, dormir=esperas.append, ahora=AHORA, log=lambda *_: None, **k)
    return r, esperas


def test_escribe_una_serie_por_nodo_y_mercado_y_descarta_el_mes_parcial(tmp_path):
    tax = _tax(2, ("CO", "MX"))
    r, _ = _correr(tax, Falso(), tmp_path)
    assert (r.total, r.descargadas) == (4, 4)
    reg = leer_serie(ruta_serie("CO", "prenda.n0", tmp_path))
    assert reg["serie"] == [["2026-07-01", 40], ["2026-08-01", 44]]  # sin el 2026-09 parcial
    assert reg["parcial_descartado"] is True
    assert (reg["nodo"], reg["mercado"], reg["consulta"], reg["backend"]) == ("prenda.n0", "CO", "q0", "falso")
    assert reg["descargado"] == "2026-09-26T12:00"


def test_una_segunda_corrida_no_vuelve_a_consultar(tmp_path):
    tax = _tax()
    _correr(tax, Falso(), tmp_path)
    b2 = Falso()
    r, _ = _correr(tax, b2, tmp_path)
    assert b2.llamadas == []
    assert (r.en_cache, r.descargadas) == (6, 0)


def test_refrescar_vuelve_a_descargar(tmp_path):
    tax = _tax(1, ("CO",))
    _correr(tax, Falso(), tmp_path)
    b2 = Falso()
    _correr(tax, b2, tmp_path, refrescar=True)
    assert len(b2.llamadas) == 1


def test_serie_vacia_se_guarda_como_sin_datos_y_no_se_repite(tmp_path):
    tax = _tax(1, ("CO",))
    r, _ = _correr(tax, Falso(filas=[]), tmp_path)
    assert r.sin_datos == 1
    assert leer_serie(ruta_serie("CO", "prenda.n0", tmp_path))["estado"] == "sin_datos"
    b2 = Falso()
    _correr(tax, b2, tmp_path)
    assert b2.llamadas == []  # ya se sabe que no hay datos; no se insiste


def test_reintenta_tras_un_error_pasajero(tmp_path):
    tax = _tax(1, ("CO",))
    b = Falso(guion=[ErrorFuente("timeout"), None])
    r, esperas = _correr(tax, b, tmp_path)
    assert r.descargadas == 1
    assert len(b.llamadas) == 2
    assert 15 in esperas  # esperó antes de reintentar


def test_el_bloqueo_429_espera_cada_vez_mas(tmp_path):
    tax = _tax(1, ("CO",))
    b = Falso(guion=[Bloqueado("429"), Bloqueado("429"), None])
    r, esperas = _correr(tax, b, tmp_path)
    assert r.descargadas == 1
    assert [e for e in esperas if e >= 60] == [60, 120]


def test_se_detiene_limpio_si_varias_series_seguidas_fallan_y_conserva_lo_hecho(tmp_path):
    tax = _tax(6, ("CO",))
    # 1 serie buena, luego bloqueo permanente
    b = Falso(guion=[None] + [Bloqueado("429")] * 100)
    r, _ = _correr(tax, b, tmp_path, reintentos=2, max_fallos_seguidos=3)
    assert r.interrumpida and "bloqueo" in r.motivo
    assert r.descargadas == 1
    assert len(r.fallidas) == 3
    assert ruta_serie("CO", "prenda.n0", tmp_path).exists()  # lo que ya estaba hecho sigue ahí
    # y al reanudar continúa desde donde quedó, sin repetir la primera
    b2 = Falso()
    r2, _ = _correr(tax, b2, tmp_path)
    assert r2.en_cache == 1 and r2.descargadas == 5
    assert ("CO", "q0") not in b2.llamadas


def test_un_exito_reinicia_la_cuenta_de_fallos_seguidos(tmp_path):
    tax = _tax(4, ("CO",))
    # falla, éxito, falla, éxito: nunca 2 seguidas
    b = Falso(guion=[ErrorFuente("x")] * 1 + [None, ErrorFuente("x"), None])
    r, _ = _correr(tax, b, tmp_path, reintentos=1, max_fallos_seguidos=2)
    assert not r.interrumpida


def test_limite_corta_tras_n_descargas_nuevas(tmp_path):
    tax = _tax(5, ("CO",))
    b = Falso()
    r, _ = _correr(tax, b, tmp_path, limite=2)
    assert len(b.llamadas) == 2 and r.interrumpida


def test_filtra_por_mercado_y_por_tipo(tmp_path):
    tax = _tax(2, ("CO", "MX"))
    b = Falso()
    _correr(tax, b, tmp_path, mercados=["MX"], tipos=["prenda"])
    assert {m for m, _ in b.llamadas} == {"MX"}


def test_no_deja_archivos_temporales(tmp_path):
    _correr(_tax(2, ("CO",)), Falso(), tmp_path)
    assert list(tmp_path.rglob("*.tmp")) == []
    json.loads(ruta_serie("CO", "prenda.n1", tmp_path).read_text(encoding="utf-8"))  # JSON válido


def test_pausa_solo_despues_de_consultas_reales(tmp_path):
    tax = _tax(2, ("CO",))
    _correr(tax, Falso(), tmp_path)
    _, esperas = _correr(tax, Falso(), tmp_path, pausa=8)
    assert esperas == []  # todo en caché: no hay nada que esperar
