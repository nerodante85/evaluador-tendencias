"""Fuente MercadoLibre — candidata de la fase 6 (docs/v2/00-decisiones.md).

Ya no es de acceso libre: hoy exige una aplicación de desarrollador
registrada (OAuth 2.0, Authorization Code). Este módulo solo resuelve la
mecánica de autenticación y el fetch de bajo nivel de los dos endpoints que
se querían evaluar (`/trends/{sitio}` y `/sites/{sitio}/search`) — todavía
NO está probado en vivo con un token real, y por eso NO se integra al
pipeline de la taxonomía hasta que se confirme, con datos reales, que la
forma de esos endpoints sirve para backtesting (el mismo criterio que ya
descartó a Pinterest Trends: dar solo un top-N del día de hoy no sirve,
aunque el acceso funcione).

Límite estructural que ya se sabe de antemano, no hace falta probarlo:
**MercadoLibre no opera en España.** Sus sitios son todos de Latinoamérica
(MCO Colombia, MLM México, MLA Argentina, MLB Brasil, etc.) — como mucho
esta fuente podría aportar señal para CO y MX, nunca para ES.

Credenciales: SIEMPRE por variable de entorno (`MELI_CLIENT_ID`,
`MELI_CLIENT_SECRET`), nunca hardcodeadas ni en el repo. Ver
`pipeline/mercadolibre_auth.py` para el flujo interactivo que las usa.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

SITIOS = {"CO": "MCO", "MX": "MLM"}  # ES queda fuera a propósito: MercadoLibre no opera ahí

URL_TOKEN = "https://api.mercadolibre.com/oauth/token"
URL_AUTORIZACION = "https://auth.mercadolibre.com.co/authorization"  # cuenta/app registrada en el sitio .com.co


class ErrorFuente(Exception):
    """Falló una consulta o un intercambio de token por una causa que puede ser pasajera."""


class Bloqueado(ErrorFuente):
    """MercadoLibre está limitando las consultas (HTTP 429)."""


class ErrorAutenticacion(ErrorFuente):
    """El token es inválido, expiró, o el intercambio del código falló (HTTP 400/401)."""


def _post_form(url, datos):
    cuerpo = urllib.parse.urlencode(datos).encode("utf-8")
    req = urllib.request.Request(
        url, data=cuerpo, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    return _ejecutar(req)


def _get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    return _ejecutar(req)


def _ejecutar(req):
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        if e.code == 429:
            raise Bloqueado(cuerpo) from e
        if e.code in (400, 401, 403):
            raise ErrorAutenticacion(f"HTTP {e.code}: {cuerpo[:300]}") from e
        raise ErrorFuente(f"HTTP {e.code}: {cuerpo[:300]}") from e
    except urllib.error.URLError as e:
        raise ErrorFuente(str(e)) from e


def url_autorizacion(client_id, redirect_uri):
    """URL que el usuario abre en su navegador para iniciar sesión y autorizar la app.
    Devuelve un `code` por query string en `redirect_uri` — se copia a mano."""
    q = urllib.parse.urlencode({"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri})
    return f"{URL_AUTORIZACION}?{q}"


def intercambiar_codigo(client_id, client_secret, code, redirect_uri):
    """Canjea el `code` de la autorización por un access_token + refresh_token.
    Devuelve el JSON crudo de MercadoLibre (incluye `expires_in`, típicamente 6h)."""
    return _post_form(URL_TOKEN, {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    })


def refrescar_token(client_id, client_secret, refresh_token):
    """Pide un access_token nuevo sin repetir el login manual."""
    return _post_form(URL_TOKEN, {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    })


class BackendMercadoLibre:
    """Devuelve el JSON crudo tal como lo entrega MercadoLibre — a propósito,
    todavía no se sabe si la forma del dato sirve para series históricas
    (ver docstring del módulo), así que no tiene sentido normalizarlo antes
    de mirarlo con datos reales, como se hizo con Wikipedia y Pinterest."""

    nombre = "mercadolibre"

    def __init__(self, access_token):
        self.access_token = access_token

    def tendencias(self, sitio):
        """GET /trends/{sitio}. `sitio` es un código de SITIOS (p. ej. "MCO")."""
        return _get(f"https://api.mercadolibre.com/trends/{sitio}", self.access_token)

    def buscar(self, sitio, consulta):
        """GET /sites/{sitio}/search?q=consulta."""
        q = urllib.parse.urlencode({"q": consulta})
        return _get(f"https://api.mercadolibre.com/sites/{sitio}/search?{q}", self.access_token)
