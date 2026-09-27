"""Historial de calibraciones del Trend Score — para poder ver si se degrada
con el tiempo (model drift), no solo el número de la última corrida.

No hay forma de saber en automático "¿acertó de verdad?" sin esperar meses
de datos reales — eso es lo que hace el backtesting, offline y a mano
(pipeline/backtesting.py). Lo que SÍ se puede hacer solo, cada vez que
alguien recalibra (`python -m pipeline.cli trend_score`), es dejar un
registro y avisar si el número se cayó de golpe contra la calibración
anterior. Hallazgo de la auditoría del 2026-09-27 (AUDIT-REPORT.md, sección
32, "Monitorización").

No decide nada por sí solo: solo registra y avisa por consola. Si hay una
caída real, la decisión de qué hacer (¿ampliar la muestra? ¿revisar la
definición de tendencia? ¿fue solo ruido de esta corrida?) sigue siendo de
Ricardo, igual que cualquier cambio de metodología en este proyecto.
"""

import json

from .taxonomia import RAIZ

RUTA_HISTORIAL = RAIZ / "data" / "v2" / "trend_score_historial.json"
CAIDA_AUC_ALERTA = 0.05  # una caída de más de esto contra la calibración anterior ya es alerta


def _leer(ruta):
    if not ruta.exists():
        return []
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return datos.get("calibraciones", [])


def _comparar(historial, entrada):
    """(alerta: bool, mensaje: str | None). Sin historial previo no hay
    contra qué comparar — no es alerta, es la primera vez que se registra."""
    if not historial:
        return False, None
    anterior = historial[-1]
    if entrada["auc"] is None or anterior["auc"] is None:
        return False, None

    caida = anterior["auc"] - entrada["auc"]
    if caida >= CAIDA_AUC_ALERTA:
        return True, (
            f"AUC bajó de {anterior['auc']} a {entrada['auc']} (−{round(caida, 3)}) "
            f"respecto a la calibración anterior ({anterior['calibrado']})."
        )

    if entrada["exactitud_mayoria"] is not None and entrada["exactitud"] < entrada["exactitud_mayoria"]:
        return True, (
            f"La exactitud ({entrada['exactitud']}) ya no supera ni la clase mayoritaria "
            f"({entrada['exactitud_mayoria']}) — el score dejó de aportar sobre adivinar."
        )

    return False, None


def registrar(pesos_dict, ruta=RUTA_HISTORIAL):
    """Agrega la calibración de HOY (append-only, nunca se reescribe una
    entrada vieja) y devuelve (alerta, mensaje) comparando contra la última
    entrada previa. `pesos_dict` es el mismo dict que ya se escribe en
    trend_score_pesos.json (ver reporte_trend_score.py::escribir_pesos)."""
    historial = _leer(ruta)
    ev = pesos_dict["evaluacion_fuera_de_muestra"]
    entrada = {
        "calibrado": pesos_dict["calibrado"],
        "n_entrenamiento": pesos_dict["n_entrenamiento"],
        "n_prueba": pesos_dict["n_prueba"],
        "auc": ev["auc"],
        "exactitud": ev["exactitud"],
        "exactitud_mayoria": ev["exactitud_mayoria"],
    }

    alerta, mensaje = _comparar(historial, entrada)

    historial.append(entrada)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"esquema": 1, "calibraciones": historial}, ensure_ascii=False, indent=1), encoding="utf-8")
    return alerta, mensaje
