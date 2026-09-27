"""Corre el backtesting (pipeline/backtesting.py) sobre una muestra de series
y escribe data/v2/backtesting.json + docs/v2/reporte-backtesting-fase3.md.

La pregunta que responde el informe: ¿algún modelo le gana de verdad al
baseline (naive estacional)? Si no, el veredicto correcto es seguir con el
baseline — no es un fracaso del proyecto, es lo que dice `comparar_contra_baseline`.
"""

import json
from datetime import datetime

from .backtesting import (
    HORIZONTES,
    MODELOS,
    agregar_por_modelo_y_horizonte,
    comparar_contra_baseline,
    correr,
    frecuencia_clase_mayoritaria,
    precision_recall_por_clase,
)
from .calidad import evaluar
from .historia import DIR_RAW, leer_serie, ruta_serie
from .taxonomia import RAIZ, cargar


def escribir_informe(agregado, veredicto, veredicto_bonferroni, mayoritaria, precision_recall, n_series, n_cortes, n_filas, ruta_md, ruta_json, hoy=None):
    hoy = hoy or datetime.now()
    modelos = list(MODELOS)
    baseline = "naive_estacional"
    n_pruebas = len([1 for h in HORIZONTES for m in modelos if m != baseline])

    L = []
    L.append("# Radar 2.0 — backtesting, fase 3")
    L.append("")
    L.append(f"Generado el {hoy.date().isoformat()} por `python -m pipeline.cli backtest`. Método: `docs/v2/01-definicion-tendencia.md` (aprobado). Código: `pipeline/backtesting.py`, `pipeline/modelos.py`.")
    L.append("")
    L.append(f"Muestra: **{n_series} series** × hasta {n_cortes} cortes cada una → **{n_filas} evaluaciones** (serie × corte × horizonte × modelo).")
    L.append("")
    L.append("## Puerta de salida: ¿algún modelo le gana al baseline?")
    L.append("")
    L.append("\"Ganarle\" no es \"tener un número más alto\" — con miles de evaluaciones hasta una diferencia de una fracción de punto sale \"mayor\" sin significar nada (pasó en la primera corrida real: 0.610 contra 0.605, un solo acierto de diferencia sobre 172 casos). Exige dos cosas sobre los mismos casos emparejados con el baseline: significancia estadística (test binomial exacto de McNemar, p < 0.05) y una diferencia de exactitud de al menos 3 puntos. No se pasa un modelo a producción sin ganarle aquí — si ninguno le gana, el panel se queda con el baseline, y esa también es una respuesta válida.")
    L.append("")
    L.append("| Horizonte | " + " | ".join(m for m in modelos if m != baseline) + " |")
    L.append("|---|" + "---|" * (len(modelos) - 1))
    for h in HORIZONTES:
        celdas = []
        for m in modelos:
            if m == baseline:
                continue
            v = veredicto.get((m, h))
            celdas.append("le gana ✓" if v else ("no le gana" if v is False else "(sin datos)"))
        L.append(f"| {h} meses | " + " | ".join(celdas) + " |")
    L.append("")
    n_ganan = sum(1 for v in veredicto.values() if v)
    n_ganan_corregido = sum(1 for v in veredicto_bonferroni.values() if v)
    L.append(f"Se corrieron **{n_pruebas} pruebas** de significancia a la vez (3 modelos × 3 horizontes), con α = 0.05 cada una — eso por sí solo deja una probabilidad real de un positivo falso por puro azar de comparar varias veces. Corrigiendo con Bonferroni (α = 0.05 / {n_pruebas} ≈ {0.05/n_pruebas:.4f}):")
    L.append("")
    if n_ganan and not n_ganan_corregido:
        L.append(f"**El resultado cambia**: {n_ganan} combinación(es) parecían ganarle al baseline sin corregir, pero **ninguna sobrevive** la corrección. La conclusión honesta de esta corrida es que, con esta muestra, ningún modelo le gana de verdad al baseline — no se adopta ninguno todavía. Ver `docs/v2/hallazgo-backtesting-fase3.md`.")
    elif n_ganan_corregido:
        sobrevivientes = ", ".join(f"{m} a {h} meses" for (m, h), v in veredicto_bonferroni.items() if v)
        L.append(f"**{n_ganan_corregido} combinación(es) sobreviven** incluso con la corrección: {sobrevivientes}.")
    else:
        L.append("Ninguna combinación le ganaba al baseline ni antes de corregir.")
    L.append("")
    L.append("## Exactitud y error por modelo y horizonte")
    L.append("")
    L.append("Exactitud = % de veces que la etiqueta pronosticada coincidió con la real. Error mediano = diferencia absoluta mediana entre el nivel futuro pronosticado y el real (escala propia de cada serie).")
    L.append("")
    L.append("La fila `(mayoría)` no es un modelo: es adivinar siempre la etiqueta real más frecuente de ese horizonte, sin mirar la serie — la vara mínima real. 25% (una de cuatro al azar) sería la referencia incorrecta si las clases estuvieran parejas; en la práctica \"estable\" domina, sobre todo a horizontes largos, así que la vara mínima real es más alta que eso.")
    L.append("")
    L.append("| Modelo | Horizonte | n | Exactitud | Error mediano |")
    L.append("|---|---:|---:|---:|---:|")
    for h in HORIZONTES:
        if h in mayoritaria:
            L.append(f"| (mayoría) | {h} | — | {round(mayoritaria[h], 3)} | — |")
    for m in modelos:
        for h in HORIZONTES:
            met = agregado.get((m, h))
            if met is None:
                continue
            L.append(f"| {m} | {h} | {met.n} | {met.exactitud} | {met.error_mediano} |")
    L.append("")
    L.append("## Precision y recall de \"alza_sostenida\" — la clase que más importa para decidir compra")
    L.append("")
    L.append("La exactitud de arriba es un promedio sobre las cuatro etiquetas; con clases desbalanceadas (`estable` domina casi todos los horizontes) puede esconder que un modelo falle sistemáticamente más en una dirección. Estas dos preguntas son distintas y le importan a decisiones distintas:")
    L.append("")
    L.append("- **Precision** — de las veces que el modelo dijo \"esto va a ser alza sostenida\", ¿cuántas eran ciertas? Precision baja = comprar por señales falsas (falso positivo).")
    L.append("- **Recall** — de las veces que la serie SÍ terminó en alza sostenida, ¿cuántas detectó el modelo? Recall bajo = dejar pasar tendencias reales (falso negativo).")
    L.append("")
    L.append("| Modelo | Horizonte | Precision | Recall | TP | FP | FN |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for m in modelos:
        for h in HORIZONTES:
            pr = precision_recall.get((m, h), {}).get("alza_sostenida")
            if pr is None:
                continue
            prec = pr["precision"] if pr["precision"] is not None else "—"
            rec = pr["recall"] if pr["recall"] is not None else "—"
            L.append(f"| {m} | {h} | {prec} | {rec} | {pr['tp']} | {pr['fp']} | {pr['fn']} |")
    L.append("")
    L.append("La matriz completa (las cuatro etiquetas, no solo `alza_sostenida`) queda en `data/v2/backtesting.json` bajo `precision_recall`.")
    ruta_md.write_text("\n".join(L), encoding="utf-8")

    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    salida = {
        "esquema": 1,
        "generado": hoy.isoformat(timespec="minutes"),
        "n_series": n_series,
        "n_cortes": n_cortes,
        "n_filas": n_filas,
        "metricas": {f"{m}|{h}": {"n": met.n, "exactitud": met.exactitud, "error_mediano": met.error_mediano} for (m, h), met in agregado.items()},
        "veredicto": {f"{m}|{h}": v for (m, h), v in veredicto.items()},
        "veredicto_bonferroni": {f"{m}|{h}": v for (m, h), v in veredicto_bonferroni.items()},
        "clase_mayoritaria": {str(h): v for h, v in mayoritaria.items()},
        "precision_recall": {f"{m}|{h}": por_clase for (m, h), por_clase in precision_recall.items()},
    }
    ruta_json.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")


def main(n_series=36, n_cortes=5, log=print):
    tax = cargar()
    calidad = evaluar(tax)
    resultados = correr(tax, calidad, DIR_RAW, leer_serie, ruta_serie, n_series=n_series, n_cortes=n_cortes, log=log)
    agregado = agregar_por_modelo_y_horizonte(resultados)
    veredicto = comparar_contra_baseline(resultados)
    n_pruebas = len([1 for h in HORIZONTES for m in MODELOS if m != "naive_estacional"])
    veredicto_bonferroni = comparar_contra_baseline(resultados, alpha=0.05 / n_pruebas)
    mayoritaria = frecuencia_clase_mayoritaria(resultados)
    precision_recall = precision_recall_por_clase(resultados)
    md = RAIZ / "docs" / "v2" / "reporte-backtesting-fase3.md"
    js = RAIZ / "data" / "v2" / "backtesting.json"
    escribir_informe(agregado, veredicto, veredicto_bonferroni, mayoritaria, precision_recall, n_series, n_cortes, len(resultados), md, js)
    log(f"\nInforme: {md}\nDatos: {js}")


if __name__ == "__main__":
    main()
