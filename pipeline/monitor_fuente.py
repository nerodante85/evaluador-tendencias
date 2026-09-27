"""Chequeo de salud de `pytrends` — no descarga nada del pipeline real.

Responde una sola pregunta: ¿`pytrends` todavía puede traer datos de Google
Trends, o ya se rompió? (docs/plan-respaldo-fuentes.md explica qué hacer si
la respuesta es "se rompió"). Una consulta chica y barata, pensada para
correr sola cada semana desde `.github/workflows/monitor-fuente.yml` — no
las 474 series reales, que tardan horas y no tiene sentido repetir solo para
saber si la fuente sigue viva.

Código de salida 0 = funciona. Código de salida 1 = no funciona (bloqueado,
o cualquier otro error) — el workflow lo usa para decidir si abre un issue.
"""

import sys

from .fuentes.trends import Bloqueado, ErrorFuente
from .taxonomia import Mercado

CONSULTA_DE_PRUEBA = "jean"  # término real y estable, no debería dar cero nunca
MERCADO_DE_PRUEBA = Mercado("CO", "Colombia", "es-CO", 300)


def chequear(backend, consulta=CONSULTA_DE_PRUEBA, mercado=MERCADO_DE_PRUEBA):
    """Devuelve (ok: bool, mensaje: str). No lanza — el llamador decide qué
    hacer con el resultado (imprimir, salir con código de error, etc.)."""
    try:
        filas = backend.interes_en_el_tiempo(consulta, mercado, timeframe="today 3-m")
    except Bloqueado as e:
        return False, f"pytrends está bloqueado (HTTP 429): {e}"
    except ErrorFuente as e:
        return False, f"pytrends falló: {e}"
    except Exception as e:  # cualquier otra cosa (ImportError de pytrends, etc.) también cuenta como "roto"
        return False, f"error inesperado consultando pytrends: {e}"

    if not filas:
        return False, f"pytrends respondió sin error, pero sin ningún dato para '{consulta}' — inusual para un término real, revisar a mano"

    return True, f"OK — {len(filas)} puntos para '{consulta}' en {mercado.codigo}"


def main():
    from .fuentes.trends import BackendPytrends

    ok, mensaje = chequear(BackendPytrends())
    print(mensaje)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
