"""Motor de señales de Radar 2.0.

Calcula, por serie mensual, las variables que van a alimentar el Trend Score
(fase 4): crecimiento, aceleración, persistencia, volatilidad, saturación y
estacionalidad. También clasifica el estado más reciente de la serie
("¿esto se ve hoy como una tendencia sostenida, un pico de atención, algo
estacional, o estable?").

La función central, `etiquetar()`, es la MISMA regla que ya aprobó Ricardo en
docs/v2/01-definicion-tendencia.md — no hay una versión "para hoy" y otra
"para el backtesting". La diferencia es solo el punto de corte:

  - Fase 2 (este módulo): se evalúa en el único corte donde el "futuro" ya
    se conoce — los últimos `horizonte` meses de la serie. Es lo que se
    puede decir HOY sin haber inventado ningún dato.
  - Fase 3 (backtesting, pendiente): el mismo `etiquetar()` se corre en
    cientos de cortes históricos, donde el futuro real de cada corte
    también quedó registrado, para medir qué tan bien predijo el sistema.

Los parámetros (umbral de crecimiento, persistencia mínima, piso de ruido,
ventana) están fijados en docs/v2/01-definicion-tendencia.md y no se tocan
aquí sin repetir ese documento.
"""

import statistics
from collections import Counter
from dataclasses import dataclass

VENTANA = 12
HORIZONTE_ACTUAL = 12
UMBRAL_CRECIMIENTO = 0.25
PERSISTENCIA_MIN = 9
PISO_RUIDO = 5
MEDIANA_ALZA = 1.15
MEDIANA_BAJA = 0.85
PICO_MULT = 2.0

ETIQUETAS = ("alza_sostenida", "baja_sostenida", "pico_atencion", "estable", "no_evaluable", "sin_ventana")


def _media(xs):
    return sum(xs) / len(xs) if xs else 0.0


@dataclass(frozen=True)
class Etiqueta:
    etiqueta: str
    corte: int
    horizonte: int
    base: float | None = None
    futuro: float | None = None
    crecimiento: float | None = None  # futuro/base' - 1
    persistencia_alza: int | None = None  # de `ventana` meses futuros, cuántos >= base
    persistencia_baja: int | None = None  # cuántos <= base
    mediana_futuro: float | None = None


def etiquetar(valores, corte, horizonte, ventana=VENTANA):
    """Clasifica el tramo que va del corte `corte` (índice 0-based, último mes
    de la ventana base) hasta `corte + horizonte` (fin de la ventana futura),
    siguiendo docs/v2/01-definicion-tendencia.md. Ambas ventanas duran
    `ventana` meses; la futura TERMINA en `corte + horizonte`, no empieza ahí.

    Devuelve "sin_ventana" si la serie no tiene los meses necesarios para
    ese corte (no es un juicio sobre la tendencia: es que no se puede medir).
    """
    inicio_base = corte - ventana + 1
    fin_futuro = corte + horizonte
    inicio_futuro = fin_futuro - ventana + 1
    if inicio_base < 0 or fin_futuro >= len(valores):
        return Etiqueta("sin_ventana", corte, horizonte)

    base = valores[inicio_base : corte + 1]
    futuro = valores[inicio_futuro : fin_futuro + 1]
    B = _media(base)
    F = _media(futuro)

    if B < PISO_RUIDO and F < PISO_RUIDO:
        return Etiqueta("no_evaluable", corte, horizonte, base=B, futuro=F)

    B_ = max(B, PISO_RUIDO)
    crecimiento = F / B_ - 1
    persistencia_alza = sum(1 for v in futuro if v >= B)
    persistencia_baja = sum(1 for v in futuro if v <= B)
    mediana_f = statistics.median(futuro)

    campos = dict(
        corte=corte, horizonte=horizonte, base=round(B, 2), futuro=round(F, 2),
        crecimiento=round(crecimiento, 4), persistencia_alza=persistencia_alza,
        persistencia_baja=persistencia_baja, mediana_futuro=round(mediana_f, 2),
    )

    if crecimiento >= UMBRAL_CRECIMIENTO and persistencia_alza >= PERSISTENCIA_MIN and mediana_f / B_ >= MEDIANA_ALZA:
        return Etiqueta("alza_sostenida", **campos)
    if crecimiento <= -UMBRAL_CRECIMIENTO and persistencia_baja >= PERSISTENCIA_MIN and mediana_f / B_ <= MEDIANA_BAJA:
        return Etiqueta("baja_sostenida", **campos)
    if max(futuro) >= PICO_MULT * B_ and persistencia_alza < PERSISTENCIA_MIN:
        return Etiqueta("pico_atencion", **campos)
    return Etiqueta("estable", **campos)


def estado_actual(valores, horizonte=HORIZONTE_ACTUAL, ventana=VENTANA):
    """El único corte donde el futuro ya se conoce: los últimos `horizonte`
    meses de la serie son la ventana "futura"; antes de eso, la base."""
    corte = len(valores) - 1 - horizonte
    return etiquetar(valores, corte, horizonte, ventana)


def aceleracion(valores, horizonte=HORIZONTE_ACTUAL, ventana=VENTANA):
    """Diferencia entre el crecimiento más reciente y el crecimiento medido
    un año antes (mismo cálculo, desplazado `horizonte` meses hacia atrás).
    Positivo = el crecimiento se está acelerando; negativo, desacelerando.
    None si no hay suficiente historia para medir el tramo anterior."""
    reciente = estado_actual(valores, horizonte, ventana)
    anterior = etiquetar(valores, len(valores) - 1 - 2 * horizonte, horizonte, ventana)
    if reciente.crecimiento is None or anterior.crecimiento is None:
        return None
    return round(reciente.crecimiento - anterior.crecimiento, 4)


def volatilidad(valores, meses=24):
    """Coeficiente de variación (desviación estándar / media) de los últimos
    `meses`. Series muy erráticas (>0.6, mismo umbral que usaba fetch_trends.py
    v1) no sostienen ninguna lectura de tendencia."""
    recientes = [v for v in valores[-meses:]]
    if len(recientes) < 3:
        return None
    media = statistics.fmean(recientes)
    if media <= 0:
        return None
    return round(statistics.pstdev(recientes) / media, 3)


def saturacion(valores, meses_recientes=12):
    """Nivel actual respecto al máximo histórico de la serie: cerca de 1 =
    ya tocó su techo (aunque siga "subiendo", tiene poco margen); cerca de 0
    = lejos de su pico. None si la serie nunca tuvo volumen (máximo 0)."""
    maximo = max(valores) if valores else 0
    if maximo <= 0:
        return None
    return round(_media(valores[-meses_recientes:]) / maximo, 3)


def _mes(fecha_iso):
    return int(fecha_iso[5:7])


def es_estacional(fechas, valores, umbral_crecimiento=UMBRAL_CRECIMIENTO):
    """¿El pico de los últimos 12 meses es de calendario, no de tendencia?

    Coincidir el mes del máximo dos años seguidos no basta: una serie que
    sube todo el tiempo también tiene su máximo al final de cada ventana.
    Por eso exige, a la vez: los meses del máximo coinciden, el pico
    sobresale de verdad sobre la mediana de su propia ventana, y no hay
    crecimiento fuerte que lo explique mejor que el calendario. Mismo
    criterio que usaba fetch_trends.py v1, adaptado a ventanas de 12 meses
    en vez de año calendario."""
    if len(valores) < 24:
        return None
    reciente_v, reciente_f = valores[-12:], fechas[-12:]
    anterior_v, anterior_f = valores[-24:-12], fechas[-24:-12]
    if max(reciente_v) <= 0 or max(anterior_v) <= 0:
        return False

    mes_reciente = _mes(reciente_f[reciente_v.index(max(reciente_v))])
    mes_anterior = _mes(anterior_f[anterior_v.index(max(anterior_v))])
    mismo_mes = mes_reciente == mes_anterior

    mediana = statistics.median(reciente_v)
    sobresale = mediana > 0 and max(reciente_v) >= mediana * 1.3

    crecimiento = estado_actual(valores).crecimiento
    sin_crecimiento_fuerte = crecimiento is None or crecimiento < umbral_crecimiento

    return bool(mismo_mes and sobresale and sin_crecimiento_fuerte)


def variables(fechas, valores):
    """Todo el motor de señales para una serie: lo que entra al Trend Score."""
    estado = estado_actual(valores)
    return {
        "etiqueta": estado.etiqueta,
        "crecimiento": estado.crecimiento,
        "persistencia": estado.persistencia_alza,
        "aceleracion": aceleracion(valores),
        "volatilidad": volatilidad(valores),
        "saturacion": saturacion(valores),
        "estacional": es_estacional(fechas, valores),
    }


def moda_calendario(fechas, valores, meses=60):
    """Mes(es) donde suele caer el máximo anual, sobre los últimos `meses`
    meses — dato de apoyo para leer estacionalidad, no parte de la etiqueta."""
    pares = list(zip(fechas[-meses:], valores[-meses:]))
    por_ano = {}
    for f, v in pares:
        ano = f[:4]
        if ano not in por_ano or v > por_ano[ano][1]:
            por_ano[ano] = (f, v)
    conteo = Counter(_mes(f) for f, _ in por_ano.values())
    return conteo.most_common()
