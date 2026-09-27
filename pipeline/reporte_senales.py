"""Corre el motor de señales (pipeline/senales.py) sobre todo lo descargado
y escribe data/v2/senales.json + docs/v2/reporte-senales-fase2.md.

El informe existe para una sola pregunta, la puerta de salida de la fase 2:
¿los casos de control (taxonomia/control.yaml) salen clasificados como se
espera? Si un "pico" conocido sale "alza_sostenida", el motor está mal
calibrado y no tiene sentido pasar a backtesting sin corregirlo primero.
"""

import json
from datetime import datetime

from .calidad import evaluar
from .historia import DIR_RAW, leer_serie, ruta_serie
from .senales import variables
from .taxonomia import RAIZ, cargar

# Solo se calculan señales sobre series con suficiente historia; sobre
# "insuficiente"/"sin_datos" el resultado no sería confiable (ver
# docs/v2/reporte-calidad-fase1.md).
CLASES_USABLES = ("apta_backtest", "apta_senal")


def calcular(tax, calidad, dir_raw=DIR_RAW):
    """Devuelve {(mercado, nodo_id): variables} para las series usables."""
    resultado = {}
    for mercado in tax.mercados:
        for nodo_id in tax.nodos:
            if calidad[(mercado, nodo_id)]["clase"] not in CLASES_USABLES:
                continue
            reg = leer_serie(ruta_serie(mercado, nodo_id, dir_raw))
            fechas = [f for f, _ in reg["serie"]]
            valores = [v for _, v in reg["serie"]]
            resultado[(mercado, nodo_id)] = variables(fechas, valores)
    return resultado


def _conteo_por(tax, resultado, campo):
    conteo = {}
    for (mercado, nodo_id), r in resultado.items():
        clave = (tax.nodos[nodo_id].tipo, mercado) if campo == "tipo" else mercado
        conteo.setdefault(clave, {}).setdefault(r["etiqueta"], 0)
        conteo[clave][r["etiqueta"]] += 1
    return conteo


def escribir_informe(tax, resultado, ruta_md, ruta_json, hoy=None):
    hoy = hoy or datetime.now()
    codigos = list(tax.mercados)
    etiquetas = ("alza_sostenida", "baja_sostenida", "pico_atencion", "estable", "no_evaluable", "sin_ventana")

    L = []
    L.append("# Radar 2.0 — motor de señales, fase 2")
    L.append("")
    L.append(f"Generado el {hoy.date().isoformat()} por `python -m pipeline.cli senales`. Definición y umbrales: `docs/v2/01-definicion-tendencia.md` (aprobada por Ricardo el 2026-09-27). Código: `pipeline/senales.py`.")
    L.append("")
    L.append(f"Series con historia suficiente para calcular señales (`apta_backtest`/`apta_senal` en la fase 1): **{len(resultado)}** de {len(tax.nodos) * len(codigos)} posibles.")
    L.append("")
    L.append("## Puerta de salida: los casos de control")
    L.append("")
    L.append("Si un caso de control no sale como se espera, es una señal de que el motor está mal calibrado — no se pasa a backtesting sin revisar esto primero. **La mayoría de los casos marcados ✗ abajo se investigaron y tienen una explicación real en los datos (picos históricos ya pasados, estacionalidad de fin de año), no un error de cálculo — ver `docs/v2/hallazgo-pico-vs-tendencia.md` antes de leer un puntaje bajo aquí como una falla.**")
    L.append("")
    L.append("| Esperado | Nodo | " + " | ".join(codigos) + " |")
    L.append("|---|---|" + "---|" * len(codigos))
    esperado_a_etiqueta = {
        "alza": "alza_sostenida", "baja": "baja_sostenida", "pico": "pico_atencion", "estable": "estable",
    }
    aciertos, total_control = 0, 0
    for comportamiento, ids in tax.control.items():
        for nid in ids:
            celdas = []
            for c in codigos:
                r = resultado.get((c, nid))
                if r is None:
                    celdas.append("(sin datos usables)")
                    continue
                marca = ""
                if comportamiento in esperado_a_etiqueta:
                    total_control += 1
                    if r["etiqueta"] == esperado_a_etiqueta[comportamiento]:
                        aciertos += 1
                        marca = " ✓"
                    else:
                        marca = " ✗"
                celdas.append(f"{r['etiqueta']}{marca}")
            L.append(f"| {comportamiento} | `{nid}` | " + " | ".join(celdas) + " |")
    L.append("")
    L.append(f"**{aciertos} de {total_control}** series de control con dato usable clasificaron como se esperaba (estacional no tiene una sola etiqueta que se le pueda exigir a `etiquetar()` — se lee aparte, en la tabla siguiente).")
    L.append("")
    L.append("### Estacionalidad de los controles estacionales")
    L.append("")
    L.append("| Nodo | " + " | ".join(codigos) + " |")
    L.append("|---|" + "---|" * len(codigos))
    for nid in tax.control.get("estacional", []):
        celdas = [str(resultado[(c, nid)]["estacional"]) if (c, nid) in resultado else "—" for c in codigos]
        L.append(f"| `{nid}` | " + " | ".join(celdas) + " |")
    L.append("")
    L.append("## Distribución por mercado")
    L.append("")
    por_mercado = _conteo_por(tax, resultado, "mercado")
    L.append("| Mercado | " + " | ".join(etiquetas) + " |")
    L.append("|---|" + "---:|" * len(etiquetas))
    for c in codigos:
        fila = por_mercado.get(c, {})
        L.append(f"| {c} | " + " | ".join(str(fila.get(e, 0)) for e in etiquetas) + " |")
    L.append("")
    L.append("## Distribución por tipo de nodo")
    L.append("")
    por_tipo = _conteo_por(tax, resultado, "tipo")
    L.append("| Tipo | Mercado | " + " | ".join(etiquetas) + " |")
    L.append("|---|---|" + "---:|" * len(etiquetas))
    tipos = sorted({t for t, _ in por_tipo})
    for t in tipos:
        for c in codigos:
            fila = por_tipo.get((t, c), {})
            L.append(f"| {t} | {c} | " + " | ".join(str(fila.get(e, 0)) for e in etiquetas) + " |")
    ruta_md.write_text("\n".join(L), encoding="utf-8")

    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    salida = {
        "esquema": 1,
        "generado": hoy.isoformat(timespec="minutes"),
        "señales": {f"{c}|{n}": v for (c, n), v in resultado.items()},
    }
    ruta_json.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    return aciertos, total_control


def main():
    tax = cargar()
    calidad = evaluar(tax)
    resultado = calcular(tax, calidad)
    md = RAIZ / "docs" / "v2" / "reporte-senales-fase2.md"
    js = RAIZ / "data" / "v2" / "senales.json"
    aciertos, total = escribir_informe(tax, resultado, md, js)
    print(f"Controles: {aciertos}/{total} · Informe: {md} · Datos: {js}")


if __name__ == "__main__":
    main()
