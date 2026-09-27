"""Calibra el Trend Score sobre datos reales y escribe:

  data/v2/trend_score_pesos.json     los pesos (versionados, con fecha)
  data/v2/trend_score.json           el score de HOY para cada serie con features completas
  docs/v2/reporte-trend-score-fase4.md  el informe: cómo se calibró y qué tan bien predice, fuera de muestra
"""

import json
from datetime import datetime

from .calidad import evaluar as evaluar_calidad
from .historia import DIR_RAW, leer_serie, ruta_serie
from .historial_metricas import registrar as registrar_historial
from .senales import ETIQUETAS
from .taxonomia import RAIZ, cargar
from .trend_score import (
    HORIZONTE_SCORE,
    VARIABLES_SCORE,
    ajustar_pesos,
    calcular_score,
    construir_dataset,
    dividir_train_test,
    evaluar,
    extraer_features,
)


def escribir_pesos(pesos, n_train, n_test, evaluacion, ruta_json, hoy):
    salida = {
        "esquema": pesos.esquema,
        "calibrado": hoy.isoformat(timespec="minutes"),
        "horizonte_meses": HORIZONTE_SCORE,
        "variables": list(pesos.variables),
        "coeficientes": pesos.coeficientes,
        "intercepto": pesos.intercepto,
        "medias": pesos.medias,
        "desvios": pesos.desvios,
        "intervalos_95": {k: list(v) for k, v in pesos.intervalos.items()},
        "alpha_regularizacion": pesos.alpha,
        "n_entrenamiento": n_train,
        "n_prueba": n_test,
        "evaluacion_fuera_de_muestra": {
            "n": evaluacion.n, "exactitud": evaluacion.exactitud,
            "exactitud_mayoria": evaluacion.exactitud_mayoria, "auc": evaluacion.auc,
        },
    }
    ruta_json.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida


def escribir_informe(pesos, n_train, n_test, evaluacion, ruta_md, hoy):
    L = []
    L.append("# Radar 2.0 — Trend Score, fase 4")
    L.append("")
    L.append(f"Generado el {hoy.date().isoformat()} por `python -m pipeline.cli trend_score`. Pesos calibrados con regresión logística regularizada (L2) sobre `pipeline/senales.py` y la misma infraestructura de `pipeline/backtesting.py` (fase 3).")
    L.append("")
    L.append(f"**Horizonte: {HORIZONTE_SCORE} meses** — el único donde la fase 3 demostró que hay señal real que capturar (holt_winters/sarima le ganan al baseline ahí). El target es binario: ¿la serie terminó en `alza_sostenida` a ese horizonte?")
    L.append("")
    L.append(f"Entrenamiento: {n_train} filas (series distintas de las de prueba). Prueba: {n_test} filas, de series que el ajuste nunca vio.")
    L.append("")
    L.append("## Puerta de salida: ¿el score predice mejor que adivinar la clase mayoritaria?")
    L.append("")
    L.append(f"- Exactitud fuera de muestra (score ≥ 50 = \"probable alza\"): **{evaluacion.exactitud}**")
    L.append(f"- Adivinar siempre la clase más común, en el mismo conjunto de prueba: **{evaluacion.exactitud_mayoria}**")
    L.append(f"- AUC (¿qué tan seguido un caso que sí fue alza recibe más puntaje que uno que no?, 0.5 = igual que azar): **{evaluacion.auc}**")
    L.append("")
    if evaluacion.auc is not None and evaluacion.auc > 0.5 and evaluacion.exactitud >= evaluacion.exactitud_mayoria:
        L.append("El score generaliza mejor que la referencia mínima en datos que no vio durante el ajuste.")
    else:
        L.append("**El score NO superó la referencia mínima fuera de muestra.** No se debería usar así todavía — ver la sección de limitaciones.")
    L.append("")
    L.append("## Pesos (sobre variables estandarizadas — comparables entre sí)")
    L.append("")
    L.append("Positivo = sube el score; negativo = lo baja. El intervalo es al 95%; si cruza el cero, esa variable no aporta con la evidencia actual (no se descarta del score por eso — es información, se reporta tal cual).")
    L.append("")
    L.append("**Antes de leer esta tabla como \"por qué\" de una señal, ver `docs/v2/hallazgo-trend-score-fase4.md`**: dos pesos salen con el signo contrario al que asumía el brief original, y uno de los dos casos es un efecto de colinealidad entre variables, no un hallazgo real — se investigó cada uno por separado.")
    L.append("")
    L.append("| Variable | Peso | Intervalo 95% |")
    L.append("|---|---:|---|")
    for v in pesos.variables:
        ic = pesos.intervalos.get(v)
        ic_txt = f"[{ic[0]}, {ic[1]}]" if ic else "(no disponible)"
        L.append(f"| {v} | {pesos.coeficientes[v]} | {ic_txt} |")
    L.append(f"| (intercepto) | {pesos.intercepto} | — |")
    L.append("")
    L.append("## Limitaciones, para no sobrevender esto")
    L.append("")
    L.append("- El tamaño de muestra es el mismo problema de la fase 3: con más series y cortes el intervalo de los pesos se va a angostar. Antes de subir esto a producción vale la pena repetir con una muestra mayor, igual que se hizo en el backtesting.")
    L.append("- El score se calibró contra `alza_sostenida` únicamente. No distingue \"buen momento para vender/liquidar\" (`baja_sostenida`) de \"nada está pasando\" (`estable`) — para eso hoy sigue sirviendo la etiqueta del motor de señales (fase 2), no este número.")
    L.append("- La estacionalidad NO entra al puntaje (una señal estacional no es mejor ni peor) — se reporta aparte y el panel (fase 5) debe mostrarla como advertencia junto al score, no mezclarla.")
    ruta_md.write_text("\n".join(L), encoding="utf-8")


def calcular_hoy(tax, calidad, dir_raw, pesos, ruta_json, hoy, clases=("apta_backtest", "apta_senal")):
    """El score de HOY (no de un corte histórico) para cada serie con datos
    suficientes. Es lo que el panel (fase 5) va a mostrar."""
    salida = {}
    for mercado in tax.mercados:
        for nodo_id in tax.nodos:
            if calidad.get((mercado, nodo_id), {}).get("clase") not in clases:
                continue
            reg = leer_serie(ruta_serie(mercado, nodo_id, dir_raw))
            fechas = [f for f, _ in reg["serie"]]
            valores = [v for _, v in reg["serie"]]
            v = extraer_features(fechas, valores, len(valores) - 1)
            if any(v.get(k) is None for k in VARIABLES_SCORE):
                continue
            salida[f"{mercado}|{nodo_id}"] = {
                "score": calcular_score(v, pesos),
                "estacional": v["estacional"],
                **{k: v[k] for k in VARIABLES_SCORE},
            }
    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    ruta_json.write_text(json.dumps({"esquema": 1, "generado": hoy.isoformat(timespec="minutes"), "señales": salida}, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida


def main(n_series=150, n_cortes=8, alpha=1.0, log=print):
    hoy = datetime.now()
    tax = cargar()
    calidad = evaluar_calidad(tax)

    filas = construir_dataset(tax, calidad, DIR_RAW, leer_serie, ruta_serie, n_series=n_series, n_cortes=n_cortes, log=log)
    train, test = dividir_train_test(filas)
    pesos = ajustar_pesos(train, alpha=alpha)
    evaluacion = evaluar(test, pesos)
    log(f"\nEntrenamiento: {len(train)} · Prueba: {len(test)} · exactitud={evaluacion.exactitud} (mayoría={evaluacion.exactitud_mayoria}) · AUC={evaluacion.auc}")

    md = RAIZ / "docs" / "v2" / "reporte-trend-score-fase4.md"
    escribir_informe(pesos, len(train), len(test), evaluacion, md, hoy)
    pesos_dict = escribir_pesos(pesos, len(train), len(test), evaluacion, RAIZ / "data" / "v2" / "trend_score_pesos.json", hoy)
    hoy_datos = calcular_hoy(tax, calidad, DIR_RAW, pesos, RAIZ / "data" / "v2" / "trend_score.json", hoy)

    alerta, mensaje_drift = registrar_historial(pesos_dict)
    log(f"Informe: {md}\nSeñales puntuadas hoy: {len(hoy_datos)}")
    if alerta:
        log(f"\n⚠ ALERTA DE DEGRADACIÓN: {mensaje_drift}")
    else:
        log(f"\nHistorial de calibraciones: {RAIZ / 'data' / 'v2' / 'trend_score_historial.json'}")


if __name__ == "__main__":
    main()
