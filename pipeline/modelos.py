"""Modelos de pronóstico para el backtesting de Radar 2.0.

Cada modelo implementa la misma firma: `modelo(valores, meses) -> lista de
`meses` valores pronosticados`, para los meses que siguen inmediatamente
después del último de `valores` (que es todo lo que el modelo puede ver —
nada de la serie real futura). El backtesting (pipeline/backtesting.py)
decide cuál se queda, comparando contra el baseline; no se elige un modelo
porque sea más sofisticado.

Prophet queda fuera por ahora (dependencia pesada, opcional según el plan
original) — se puede agregar como quinto modelo si el backtesting muestra
que los de acá no alcanzan.
"""

import statistics
import warnings

PISO = 0.1  # los modelos multiplicativos/log necesitan valores > 0; Trends nunca da negativos


def _es_degenerada(valores, umbral=1.0):
    """Una serie casi constante puede colgar (no solo fallar) a Holt-Winters
    y SARIMA: al diferenciar para quitar la estacionalidad queda en puro
    cero, y el optimizador se queda buscando un mínimo que no existe.
    Se detectó corriendo las pruebas — ver pipeline/tests/test_modelos.py,
    `test_holt_winters_no_revienta_con_serie_totalmente_plana_en_cero` y su
    equivalente de sarima, que antes de esta guarda de verdad se colgaban."""
    if len(valores) < 2:
        return True
    return statistics.pstdev(valores) < umbral


def naive_estacional(valores, meses):
    """Baseline: repite el mismo mes del año anterior (si hay 12 meses de
    historia; si no, repite el último valor conocido). Es el punto de
    comparación de todo lo demás — no un modelo "simple" descartable."""
    if len(valores) < 12:
        v = valores[-1] if valores else 0
        return [v] * meses
    return [valores[-12 + (i % 12)] for i in range(meses)]


def media_movil(valores, meses, ventana=12):
    """Promedio de los últimos `ventana` meses, proyectado plano. No
    aprende tendencia ni estacionalidad — el segundo baseline más simple."""
    base = valores[-ventana:] if len(valores) >= ventana else valores
    nivel = sum(base) / len(base) if base else 0.0
    return [nivel] * meses


def holt_winters(valores, meses):
    """Suavizado exponencial con tendencia y estacionalidad aditivas
    (statsmodels). Cae a media_movil si hay poca historia o si el ajuste
    falla — un modelo que no converge no debe tumbar todo el backtesting."""
    if len(valores) < 24 or _es_degenerada(valores):
        return media_movil(valores, meses)
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        serie = [max(v, PISO) for v in valores]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ajuste = ExponentialSmoothing(
                serie, trend="add", seasonal="add", seasonal_periods=12, initialization_method="estimated"
            ).fit()
            pronostico = ajuste.forecast(meses)
        return [max(0.0, float(v)) for v in pronostico]
    except Exception:
        return media_movil(valores, meses)


def sarima(valores, meses, orden=(1, 1, 1), orden_estacional=(1, 1, 1, 12)):
    """SARIMA (statsmodels SARIMAX). Necesita más historia que Holt-Winters
    para que el término estacional (1,1,1,12) tenga sentido; igual que los
    demás, cae a media_movil si falla."""
    if len(valores) < 48 or _es_degenerada(valores):
        return media_movil(valores, meses)
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ajuste = SARIMAX(
                [float(v) for v in valores], order=orden, seasonal_order=orden_estacional,
                enforce_stationarity=False, enforce_invertibility=False,
            ).fit(disp=False)
            pronostico = ajuste.forecast(meses)
        return [max(0.0, float(v)) for v in pronostico]
    except Exception:
        return media_movil(valores, meses)


# Orden estable (para reportes e iteración); "naive_estacional" siempre
# primero porque es el baseline contra el que se miden los demás.
MODELOS = {
    "naive_estacional": naive_estacional,
    "media_movil": media_movil,
    "holt_winters": holt_winters,
    "sarima": sarima,
}
