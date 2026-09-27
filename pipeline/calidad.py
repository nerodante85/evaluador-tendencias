"""Informe de calidad de la historia descargada.

Responde la pregunta que cierra la fase 1: de los nodos de la taxonomía, ¿cuáles
tienen datos que sirvan, y para qué? No decide nada sobre el mercado — solo
dice si una serie tiene volumen y longitud suficientes para ser leída, y si
alcanza para el backtesting de 24 meses.

Umbrales (documentados en docs/v2/01-definicion-tendencia.md, escala propia
de cada serie de 0 a 100):

  apta_backtest  ≥ 120 meses de historia útil, media de los últimos 36 meses
                 ≥ 8 y como mucho 10 % de meses en cero en los últimos 60.
  apta_senal     ≥ 36 meses de historia útil, media de los últimos 24 meses
                 ≥ 5 y como mucho 25 % de meses en cero en los últimos 36.
  insuficiente   tiene datos pero no llega a lo anterior.
  sin_datos      Trends no devolvió nada, o la serie no se ha descargado.

"Historia útil" arranca en el primer mes con valor ≥ 3 dentro de la primera
ventana de 12 meses cuya media es ≥ 3: antes de eso la serie es ruido de bajo
volumen y no cuenta como historia.
"""

import json
from datetime import date, datetime

from .historia import DIR_RAW, leer_serie, ruta_serie
from .taxonomia import RAIZ

PISO_RUIDO = 3
BACKTEST = {"meses": 120, "media36": 8, "ceros60": 0.10}
SENAL = {"meses": 36, "media24": 5, "ceros36": 0.25}

CLASES = ("apta_backtest", "apta_senal", "insuficiente", "sin_datos")


def _media(xs):
    return sum(xs) / len(xs) if xs else 0.0


def metricas(valores):
    """Métricas de una serie mensual (lista de enteros, del más viejo al más nuevo)."""
    n = len(valores)
    # Media móvil de los 12 meses que TERMINAN en el mes i. La historia útil
    # empieza en el primer mes con volumen real (>= piso) dentro de la primera
    # ventana que cruza el piso: así una serie que arranca tarde no se lleva
    # de regalo los meses de ruido que la preceden.
    inicio = None
    for i in range(11, n):
        if _media(valores[i - 11 : i + 1]) >= PISO_RUIDO:
            inicio = next(j for j in range(i - 11, i + 1) if valores[j] >= PISO_RUIDO)
            break
    ultimos60 = valores[-60:]
    ultimos36 = valores[-36:]
    return {
        "meses": n,
        "meses_utiles": (n - inicio) if inicio is not None else 0,
        "media24": round(_media(valores[-24:]), 1),
        "media36": round(_media(ultimos36), 1),
        "ceros36": round(sum(1 for v in ultimos36 if v == 0) / len(ultimos36), 3) if ultimos36 else 1.0,
        "ceros60": round(sum(1 for v in ultimos60 if v == 0) / len(ultimos60), 3) if ultimos60 else 1.0,
    }


def clasificar(m):
    if m["meses"] == 0:
        return "sin_datos"
    if (
        m["meses_utiles"] >= BACKTEST["meses"]
        and m["media36"] >= BACKTEST["media36"]
        and m["ceros60"] <= BACKTEST["ceros60"]
    ):
        return "apta_backtest"
    if (
        m["meses_utiles"] >= SENAL["meses"]
        and m["media24"] >= SENAL["media24"]
        and m["ceros36"] <= SENAL["ceros36"]
    ):
        return "apta_senal"
    return "insuficiente"


def evaluar(tax, dir_raw=DIR_RAW):
    """Lee lo descargado y devuelve {(mercado, nodo_id): {"clase", "estado", **metricas}}."""
    resultado = {}
    for mercado in tax.mercados:
        for nodo in tax.nodos.values():
            ruta = ruta_serie(mercado, nodo.id, dir_raw)
            if not ruta.exists():
                resultado[(mercado, nodo.id)] = {"clase": "sin_datos", "estado": "no_descargada", **metricas([])}
                continue
            reg = leer_serie(ruta)
            valores = [v for _, v in reg["serie"]]
            m = metricas(valores)
            resultado[(mercado, nodo.id)] = {"clase": clasificar(m), "estado": reg["estado"], **m}
    return resultado


def resumen(tax, resultado):
    """Conteos por mercado y por tipo × mercado."""
    por_mercado = {c: {k: 0 for k in CLASES} for c in tax.mercados}
    por_tipo = {}
    for (mercado, nodo_id), r in resultado.items():
        por_mercado[mercado][r["clase"]] += 1
        tipo = tax.nodos[nodo_id].tipo
        por_tipo.setdefault((tipo, mercado), {k: 0 for k in CLASES})[r["clase"]] += 1
    return por_mercado, por_tipo


def escribir_informe(tax, resultado, ruta_md, ruta_json, hoy=None):
    hoy = hoy or date.today()
    por_mercado, por_tipo = resumen(tax, resultado)
    codigos = list(tax.mercados)
    L = []
    L.append("# Radar 2.0 — calidad de los datos, fase 1")
    L.append("")
    L.append(f"Generado el {hoy.isoformat()} por `python -m pipeline.cli calidad`. Es un informe de datos, sin interpretación: la lectura está en `docs/v2/00-decisiones.md`.")
    L.append("")
    L.append(f"Nodos en la taxonomía: **{len(tax.nodos)}** · mercados: {', '.join(codigos)} · series posibles: {len(tax.nodos) * len(codigos)}.")
    L.append("")
    L.append("Clases: `apta_backtest` (sirve para validar proyecciones a 24 meses), `apta_senal` (sirve para leer la señal actual pero no para backtestear), `insuficiente` (hay datos, pero poco volumen o poca historia), `sin_datos` (Trends no devolvió nada o falta descargar). Umbrales en `pipeline/calidad.py`.")
    L.append("")
    L.append("## Por mercado")
    L.append("")
    L.append("| Mercado | " + " | ".join(CLASES) + " |")
    L.append("|---|" + "---:|" * len(CLASES))
    for c in codigos:
        L.append(f"| {c} | " + " | ".join(str(por_mercado[c][k]) for k in CLASES) + " |")
    L.append("")
    L.append("## Por tipo de nodo")
    L.append("")
    L.append("Cada celda: `apta_backtest / apta_senal / insuficiente / sin_datos`.")
    L.append("")
    L.append("| Tipo | " + " | ".join(codigos) + " |")
    L.append("|---|" + "---|" * len(codigos))
    tipos = sorted({t for t, _ in por_tipo})
    for t in tipos:
        celdas = []
        for c in codigos:
            d = por_tipo.get((t, c), {k: 0 for k in CLASES})
            celdas.append(" / ".join(str(d[k]) for k in CLASES))
        L.append(f"| {t} | " + " | ".join(celdas) + " |")
    L.append("")
    L.append("## Casos de control")
    L.append("")
    L.append("Series con comportamiento conocido (`taxonomia/control.yaml`). Si no tienen datos utilizables, no sirven para sanear el método.")
    L.append("")
    L.append("| Esperado | Nodo | " + " | ".join(codigos) + " |")
    L.append("|---|---|" + "---|" * len(codigos))
    for comportamiento, ids in tax.control.items():
        for nid in ids:
            L.append(f"| {comportamiento} | `{nid}` | " + " | ".join(resultado[(c, nid)]["clase"] for c in codigos) + " |")
    L.append("")
    L.append("## Nodos por revisar")
    L.append("")
    L.append("Nodos sin datos o insuficientes en un mercado: candidatos a cambiar de consulta (el problema suele ser la consulta, no la tendencia).")
    L.append("")
    for c in codigos:
        malos = [n for n in tax.nodos if resultado[(c, n)]["clase"] in ("insuficiente", "sin_datos")]
        L.append(f"### {c} ({len(malos)})")
        L.append("")
        if malos:
            for n in malos:
                r = resultado[(c, n)]
                L.append(f"- `{n}` — «{tax.nodos[n].consultas[c]}» — {r['clase']}" + (f" (media36 {r['media36']}, {r['meses_utiles']} meses útiles)" if r["estado"] != "no_descargada" and r["estado"] != "sin_datos" else f" ({r['estado']})"))
        else:
            L.append("Ninguno.")
        L.append("")
    ruta_md.write_text("\n".join(L), encoding="utf-8")

    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    salida = {
        "esquema": 1,
        "generado": datetime.now().isoformat(timespec="minutes"),
        "series": {f"{c}|{n}": {k: v for k, v in r.items()} for (c, n), r in resultado.items()},
    }
    ruta_json.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
