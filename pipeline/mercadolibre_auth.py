"""Flujo interactivo de autorización de MercadoLibre — fase 6, exploratorio.

Se corre a mano, una vez, desde tu propia terminal (necesita que abras una
URL, inicies sesión con tu cuenta de MercadoLibre y pegues de vuelta el
`code` que llega por la URL de redirect):

    $env:MELI_CLIENT_ID = "..."
    $env:MELI_CLIENT_SECRET = "..."
    python -m pipeline.cli mercadolibre-auth --sitio MCO

Guarda el token en `data/v2/.secretos/mercadolibre_tokens.json` (gitignored,
nunca se sube) y de una vez prueba en vivo `/trends/{sitio}` y
`/sites/{sitio}/search` para ver la FORMA real del dato — todavía no se sabe
si sirve para series históricas (ver docstring de `fuentes/mercadolibre.py`).
"""

import json
import os
from pathlib import Path

from .fuentes.mercadolibre import BackendMercadoLibre, ErrorFuente, intercambiar_codigo, url_autorizacion

RAIZ = Path(__file__).resolve().parent.parent
DIR_SECRETOS = RAIZ / "data" / "v2" / ".secretos"
ARCHIVO_TOKENS = DIR_SECRETOS / "mercadolibre_tokens.json"
REDIRECT_URI_DEFECTO = "https://nerodante85.github.io/evaluador-tendencias/"

CONSULTAS_DIAGNOSTICO = ["jean", "chaqueta cuero", "crop top"]


def main(sitio="MCO"):
    client_id = os.environ.get("MELI_CLIENT_ID")
    client_secret = os.environ.get("MELI_CLIENT_SECRET")
    redirect_uri = os.environ.get("MELI_REDIRECT_URI", REDIRECT_URI_DEFECTO)
    if not client_id or not client_secret:
        print("Faltan MELI_CLIENT_ID y/o MELI_CLIENT_SECRET como variables de entorno de esta sesión.")
        print('  $env:MELI_CLIENT_ID = "tu Client ID"')
        print('  $env:MELI_CLIENT_SECRET = "tu Secret Key"')
        return 1

    print("1. Abre esta URL en tu navegador (con la cuenta que registró la app) y autoriza:\n")
    print(f"   {url_autorizacion(client_id, redirect_uri)}\n")
    print("2. Vas a caer en la página del Radar con `?code=...` en la URL — copia solo ese valor.\n")
    code = input("Pega aquí el code: ").strip()
    if not code:
        print("No llegó ningún code. Cancelado.")
        return 1

    try:
        tokens = intercambiar_codigo(client_id, client_secret, code, redirect_uri)
    except ErrorFuente as e:
        print(f"Falló el intercambio del code por un token: {e}")
        return 1

    DIR_SECRETOS.mkdir(parents=True, exist_ok=True)
    ARCHIVO_TOKENS.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"\nToken guardado en {ARCHIVO_TOKENS} (no se sube al repo). Expira en {tokens.get('expires_in')} s.")

    backend = BackendMercadoLibre(tokens["access_token"])
    print(f"\n3. Probando en vivo contra el sitio {sitio}...\n")

    try:
        tendencias = backend.tendencias(sitio)
        print(f"GET /trends/{sitio} -> {len(tendencias) if isinstance(tendencias, list) else '?'} elementos")
        print(json.dumps(tendencias[:5] if isinstance(tendencias, list) else tendencias, indent=2, ensure_ascii=False)[:1500])
    except ErrorFuente as e:
        print(f"GET /trends/{sitio} falló: {e}")

    print()
    for consulta in CONSULTAS_DIAGNOSTICO:
        try:
            r = backend.buscar(sitio, consulta)
            claves = list(r.keys()) if isinstance(r, dict) else "?"
            total = r.get("paging", {}).get("total") if isinstance(r, dict) else None
            print(f'GET /sites/{sitio}/search?q="{consulta}" -> claves de nivel superior: {claves} · total: {total}')
        except ErrorFuente as e:
            print(f'GET /sites/{sitio}/search?q="{consulta}" falló: {e}')

    print("\nPega toda esta salida (menos el token, que ya quedó guardado aparte) de vuelta en el chat para documentar el hallazgo real.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "MCO"))
