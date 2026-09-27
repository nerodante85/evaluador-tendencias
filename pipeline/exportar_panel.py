"""Consolida todo lo de Radar 2.0 (taxonomía + calidad + señales + Trend
Score + backtesting) en un solo archivo que el panel (fase 5) lee directo:

    src/data/v2/catalogo.json

Mismo patrón que la v1: el script escribe, el panel solo lee — Dashboard V2
no importa nada de pipeline/, ni de Python.

No toca nada de la v1: src/data/trends.json, src/data/macro.json,
trends_config.json, engine.js, Dashboard.jsx quedan exactamente igual.
"""

import json
from datetime import datetime

from .calidad import evaluar as evaluar_calidad
from .historia import DIR_RAW, leer_serie, ruta_serie
from .senales import estado_actual
from .taxonomia import RAIZ, cargar

RUTA_TREND_SCORE = RAIZ / "data" / "v2" / "trend_score.json"
RUTA_PESOS = RAIZ / "data" / "v2" / "trend_score_pesos.json"
RUTA_BACKTESTING = RAIZ / "data" / "v2" / "backtesting.json"
RUTA_CATALOGO = RAIZ / "src" / "data" / "v2" / "catalogo.json"

CLASES_CON_DATOS = ("apta_backtest", "apta_senal")


def _cargar_json(ruta):
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def _momentum_reciente(valores, meses=12):
    recientes = valores[-meses:]
    return round(sum(recientes) / len(recientes), 1) if recientes else 0.0


def construir_catalogo(tax, calidad, trend_score, dir_raw=DIR_RAW, leer_serie=leer_serie, ruta_serie=ruta_serie):
    nodos = {}
    for nodo_id, nodo in tax.nodos.items():
        por_mercado = {}
        for mercado in tax.mercados:
            clase = calidad.get((mercado, nodo_id), {}).get("clase")
            if clase not in CLASES_CON_DATOS:
                continue
            clave_score = f"{mercado}|{nodo_id}"
            score_info = trend_score["señales"].get(clave_score) if trend_score else None

            reg = leer_serie(ruta_serie(mercado, nodo_id, dir_raw))
            valores = [v for _, v in reg["serie"]]
            estado = estado_actual(valores)

            por_mercado[mercado] = {
                "calidad": clase,
                "momentum": _momentum_reciente(valores),
                "estado_actual": estado.etiqueta,
                "score_24m": score_info["score"] if score_info else None,
                "crecimiento": score_info["crecimiento"] if score_info else estado.crecimiento,
                "persistencia": score_info["persistencia"] if score_info else estado.persistencia_alza,
                "aceleracion": score_info["aceleracion"] if score_info else None,
                "volatilidad": score_info["volatilidad"] if score_info else None,
                "saturacion": score_info["saturacion"] if score_info else None,
                "estacional": score_info["estacional"] if score_info else None,
                "query": nodo.consultas.get(mercado),
            }

        if not por_mercado:
            continue  # sin datos usables en ningún mercado: no entra al catálogo

        nodos[nodo_id] = {
            "tipo": nodo.tipo,
            "nombre": nodo.nombre,
            "padre": nodo.padre,
            "relaciones": list(nodo.relaciones),
            "hex": nodo.hex,
            "familia": nodo.familia,
            "v1": list(nodo.v1),
            "mercados": por_mercado,
        }
    return nodos


def construir_metodologia(pesos, backtesting):
    salida = {"trend_score": None, "backtesting": None}
    if pesos:
        salida["trend_score"] = {
            "horizonte_meses": pesos["horizonte_meses"],
            "variables": pesos["variables"],
            "coeficientes": pesos["coeficientes"],
            # Para que el panel pueda distinguir una variable con respaldo
            # estadístico real de una cuyo intervalo cruza cero (ver hallazgo
            # H-04 de la auditoría del 2026-09-27 y docs/v2/hallazgo-trend-score-fase4.md):
            # la lista de "Evidencia" no debe presentar crecimiento/aceleración
            # como si explicaran el puntaje cuando su propio intervalo dice que
            # no aportan con la evidencia actual.
            "intervalos_95": pesos.get("intervalos_95", {}),
            "n_entrenamiento": pesos["n_entrenamiento"],
            "n_prueba": pesos["n_prueba"],
            "evaluacion": pesos["evaluacion_fuera_de_muestra"],
            "calibrado": pesos["calibrado"],
        }
    if backtesting:
        salida["backtesting"] = {
            "n_series": backtesting["n_series"],
            "n_cortes": backtesting["n_cortes"],
            "n_filas": backtesting["n_filas"],
            "metricas": backtesting["metricas"],
            "veredicto_bonferroni": backtesting["veredicto_bonferroni"],
            "clase_mayoritaria": backtesting.get("clase_mayoritaria", {}),
            "generado": backtesting["generado"],
        }
    return salida


def main(log=print):
    tax = cargar()
    calidad = evaluar_calidad(tax)
    trend_score = _cargar_json(RUTA_TREND_SCORE)
    pesos = _cargar_json(RUTA_PESOS)
    backtesting = _cargar_json(RUTA_BACKTESTING)

    nodos = construir_catalogo(tax, calidad, trend_score)
    metodologia = construir_metodologia(pesos, backtesting)

    salida = {
        "esquema": 1,
        "generado": datetime.now().isoformat(timespec="minutes"),
        "mercados": {c: m.nombre for c, m in tax.mercados.items()},
        "tipos": ["prenda", "corte", "tela", "color", "estampado", "estilo"],
        "metodologia": metodologia,
        "nodos": nodos,
    }

    RUTA_CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    RUTA_CATALOGO.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    if log:
        log(f"{len(nodos)} nodos con datos usables en al menos un mercado.")
        log(f"Catálogo: {RUTA_CATALOGO}")


if __name__ == "__main__":
    main()
