"""Línea de comandos del pipeline de Radar 2.0.

    python -m pipeline.cli validar
    python -m pipeline.cli historia [--mercados CO,MX] [--tipos color,tela] [--limite 6] [--refrescar]
    python -m pipeline.cli calidad

`historia` es reanudable: si se corta (o Google bloquea), volver a correr el
mismo comando continúa donde quedó.
"""

import argparse
import sys

from .calidad import escribir_informe, evaluar
from .historia import DIR_RAW, descargar_historia
from .fuentes.trends import BackendPytrends
from .reporte_senales import main as senales_main
from .taxonomia import RAIZ, cargar, validar


def _lista(texto):
    return [x.strip() for x in texto.split(",") if x.strip()] if texto else None


def main(argv=None):
    # En Windows la consola usa cp1252 por defecto y las consultas llevan tildes.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(prog="pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validar", help="valida la taxonomía")
    h = sub.add_parser("historia", help="descarga la historia larga de Trends")
    h.add_argument("--mercados", help="p. ej. CO,MX (por defecto todos)")
    h.add_argument("--tipos", help="p. ej. color,tela (por defecto todos)")
    h.add_argument("--limite", type=int, help="máximo de descargas nuevas (para probar)")
    h.add_argument("--refrescar", action="store_true", help="volver a descargar aunque ya exista")
    sub.add_parser("calidad", help="genera el informe de calidad")
    sub.add_parser("senales", help="corre el motor de señales (fase 2) y genera su informe")
    a = p.parse_args(argv)

    tax = cargar()

    if a.cmd == "validar":
        problemas = validar(tax)
        print(f"{len(tax.nodos)} nodos, {len(tax.mercados)} mercados.")
        for x in problemas:
            print(f"  - {x}")
        print("Taxonomía válida." if not problemas else f"{len(problemas)} problema(s).")
        return 1 if problemas else 0

    if a.cmd == "historia":
        problemas = validar(tax)
        if problemas:
            print("La taxonomía tiene problemas; corrígelos antes de descargar:")
            for x in problemas:
                print(f"  - {x}")
            return 1
        r = descargar_historia(
            tax,
            BackendPytrends(),
            mercados=_lista(a.mercados),
            tipos=_lista(a.tipos),
            limite=a.limite,
            refrescar=a.refrescar,
        )
        print(f"\nTotal {r.total} · ya en caché {r.en_cache} · descargadas {r.descargadas} · sin datos {r.sin_datos} · fallidas {len(r.fallidas)}")
        if r.interrumpida:
            print(f"Interrumpida: {r.motivo}")
        return 0

    if a.cmd == "calidad":
        resultado = evaluar(tax)
        md = RAIZ / "docs" / "v2" / "reporte-calidad-fase1.md"
        js = RAIZ / "data" / "v2" / "calidad.json"
        escribir_informe(tax, resultado, md, js)
        print(f"Informe: {md}\nDatos: {js}")
        return 0

    if a.cmd == "senales":
        senales_main()
        return 0


if __name__ == "__main__":
    sys.exit(main())
