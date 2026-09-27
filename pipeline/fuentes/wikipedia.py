"""Fuente Wikipedia Pageviews — candidata de la fase 6 (docs/v2/00-decisiones.md).

Gratis, sin llave, sin registro. Pero **no se integró al pipeline de la
taxonomía** (ver docs/v2/revision-fuentes-fase6.md): la búsqueda automática
de artículos no resuelve bien términos de moda específicos ("streetwear"
encuentra "Streeterville"; "pantalón cargo" encuentra "pantalón corto") y
muchos cortes/estéticas de nicho simplemente no tienen artículo propio en
Wikipedia en español. Este módulo solo hace el fetch de bajo nivel, probado
en vivo y listo para el día que exista una lista curada a mano de
`nodo -> título exacto de artículo` (una decisión editorial, no automática —
el mismo principio que ya rige trends_config.json).

Otra limitación estructural, distinta a la anterior: las vistas de página no
se pueden filtrar por país. "es.wikipedia" agrupa lectores de España,
México, Colombia y cualquier otro hispanohablante — esta fuente, si se usa,
sería una señal única "de habla hispana", no una por mercado como Trends.
"""

import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "RadarTendencias-Fase6/0.1 (github.com/nerodante85/evaluador-tendencias)"
PROYECTO = "es.wikipedia"  # una sola Wikipedia para los tres mercados; ver limitación de geo arriba


class ErrorFuente(Exception):
    """Falló una consulta por una causa que puede ser pasajera."""


class Bloqueado(ErrorFuente):
    """Wikimedia está limitando las consultas (HTTP 429)."""


class SinArticulo(ErrorFuente):
    """El artículo no existe con ese título exacto, o no hay datos en ese rango (HTTP 404)."""


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Bloqueado(str(e)) from e
        if e.code == 404:
            raise SinArticulo(str(e)) from e
        raise ErrorFuente(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}") from e
    except urllib.error.URLError as e:
        raise ErrorFuente(str(e)) from e


class BackendWikipediaPageviews:
    nombre = "wikipedia_pageviews"

    def __init__(self, proyecto=PROYECTO, pausa=1.0):
        self.proyecto = proyecto
        self.pausa = pausa  # cortesía con la API — no hay límite documentado estricto, pero es gratis y compartida

    def vistas_mensuales(self, titulo_articulo, inicio, fin):
        """`titulo_articulo` es el título EXACTO de Wikipedia (con guiones
        bajos por espacios está bien, se codifica igual). `inicio`/`fin` en
        formato YYYYMMDDHH (Wikimedia exige la hora, siempre "00").
        Devuelve [{"fecha": "AAAA-MM-01", "vistas": int}, ...] o [] si el
        artículo no existe o no hay datos en ese rango."""
        articulo = urllib.parse.quote(titulo_articulo.replace(" ", "_"), safe="")
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"{self.proyecto}/all-access/user/{articulo}/monthly/{inicio}/{fin}"
        )
        try:
            _, cuerpo = _get(url)
        except SinArticulo:
            return []
        import json

        items = json.loads(cuerpo)["items"]
        time.sleep(self.pausa)
        return [{"fecha": f"{it['timestamp'][:4]}-{it['timestamp'][4:6]}-01", "vistas": it["views"]} for it in items]
