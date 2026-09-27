"""Trend Score de Radar 2.0.

Un solo número (0-100) que resume qué tan buena es la evidencia detrás de
una señal, a partir de las variables del motor de señales (fase 2):
crecimiento, aceleración, persistencia, volatilidad y saturación.
Estacionalidad se reporta aparte como advertencia — una señal estacional
no es mejor ni peor, es un contexto distinto que el panel debe mostrar,
no mezclar en el puntaje.

Los pesos NO se ponen a mano (docs/v2/00-decisiones.md, "no pondría pesos
arbitrarios"). Se calibran con regresión logística regularizada (L2)
entrenada sobre la misma infraestructura del backtesting de la fase 3:
¿qué tan bien predicen estas cinco variables, medidas en el momento T con
datos que ya se conocían, que la señal esté en `alza_sostenida` 24 meses
después? Ese horizonte se eligió porque es el único donde la fase 3
demostró que hay algo real que capturar (holt_winters/sarima le ganan al
baseline ahí) — no tendría sentido calibrar un score contra un horizonte
donde ni los modelos de pronóstico aportan.

El ajuste se valida con una partición entrenamiento/prueba separada por
SERIE, no por fila: varias filas de la misma serie (distintos cortes)
están correlacionadas, y mezclarlas entre entrenamiento y prueba
infla artificialmente qué tan bien "generaliza" el modelo.
"""

import math
import random
from dataclasses import dataclass, field

from .backtesting import cortes_de_prueba, muestra_estratificada
from .senales import etiquetar, variables

HORIZONTE_SCORE = 24  # el único horizonte donde la fase 3 validó que hay señal real que capturar
VARIABLES_SCORE = ("crecimiento", "aceleracion", "persistencia", "volatilidad", "saturacion")
ESQUEMA = 1


@dataclass(frozen=True)
class Fila:
    mercado: str
    nodo: str
    corte: int
    features: dict  # {nombre_variable: valor float}, ya sin None
    estacional: bool | None
    alza: bool  # target: ¿la etiqueta REAL a HORIZONTE_SCORE fue alza_sostenida?


def extraer_features(fechas, valores, corte):
    """Las variables del motor de señales, medidas usando SOLO datos hasta
    `corte` (nunca después) — la serie se trunca antes de llamar a
    `senales.variables()`, que siempre lee el final de lo que se le pasa
    como "ahora"."""
    return variables(fechas[: corte + 1], valores[: corte + 1])


def construir_dataset(tax, calidad, dir_raw, leer_serie, ruta_serie, n_series=150, n_cortes=8, horizonte=HORIZONTE_SCORE, log=print):
    """Recorre una muestra de series y arma una fila por (serie, corte) con
    las features conocidas en ese momento y si la serie terminó en
    alza_sostenida `horizonte` meses después. Filas con alguna feature
    faltante (poca historia para aceleración/volatilidad/saturación) se
    descartan — es más simple y más honesto que inventar un valor."""
    from .calidad import inicio_historia_util

    muestra = muestra_estratificada(tax, calidad, n_series)
    filas = []
    descartadas = 0
    for i, (mercado, nodo_id) in enumerate(muestra, 1):
        reg = leer_serie(ruta_serie(mercado, nodo_id, dir_raw))
        fechas = [f for f, _ in reg["serie"]]
        valores = [v for _, v in reg["serie"]]
        inicio_util = inicio_historia_util(valores)
        cortes = cortes_de_prueba(len(valores), inicio_util, n_cortes, meses_max=horizonte)
        for corte in cortes:
            e_real = etiquetar(valores, corte, horizonte)
            if e_real.etiqueta not in ("alza_sostenida", "baja_sostenida", "pico_atencion", "estable"):
                continue
            v = extraer_features(fechas, valores, corte)
            faltantes = [k for k in VARIABLES_SCORE if v.get(k) is None]
            if faltantes:
                descartadas += 1
                continue
            filas.append(Fila(mercado, nodo_id, corte, {k: v[k] for k in VARIABLES_SCORE}, v["estacional"], e_real.etiqueta == "alza_sostenida"))
        if log:
            log(f"[{i}/{len(muestra)}] {mercado} {nodo_id}: {len(cortes)} corte(s)")
    if log:
        log(f"\n{len(filas)} filas utilizables, {descartadas} descartadas por features incompletas.")
    return filas


def dividir_train_test(filas, frac_train=0.7, semilla=42):
    """Separa por (mercado, nodo) completo, no por fila — para que ninguna
    serie aporte filas a la vez a entrenamiento y a prueba."""
    series = sorted({(f.mercado, f.nodo) for f in filas})
    rng = random.Random(semilla)
    rng.shuffle(series)
    corte = round(len(series) * frac_train)
    train_series = set(series[:corte])
    train = [f for f in filas if (f.mercado, f.nodo) in train_series]
    test = [f for f in filas if (f.mercado, f.nodo) not in train_series]
    return train, test


@dataclass
class Pesos:
    variables: tuple
    coeficientes: dict  # {variable: peso}
    intercepto: float
    medias: dict  # para estandarizar una feature nueva igual que en el ajuste
    desvios: dict
    intervalos: dict = field(default_factory=dict)  # {variable: (lo, hi)} al 95%
    alpha: float = 1.0
    esquema: int = ESQUEMA


def _estandarizar(filas, variables_, medias=None, desvios=None):
    medias = medias or {v: sum(f.features[v] for f in filas) / len(filas) for v in variables_}
    if desvios is None:
        desvios = {}
        for v in variables_:
            var = sum((f.features[v] - medias[v]) ** 2 for f in filas) / len(filas)
            desvios[v] = math.sqrt(var) or 1.0  # evita dividir por cero si una variable no varía
    return medias, desvios


def ajustar_pesos(filas_train, variables_=VARIABLES_SCORE, alpha=1.0):
    """Regresión logística con regularización L2 (statsmodels: fit_regularized
    con L1_wt=0 es Ridge, no Lasso — no queremos que una variable quede en
    cero solo por la regularización, las cinco tienen respaldo conceptual
    del brief original). Devuelve los pesos ya en la escala de las features
    estandarizadas (media 0, desvío 1) para que sean comparables entre sí."""
    import numpy as np
    import statsmodels.api as sm

    medias, desvios = _estandarizar(filas_train, variables_)
    X = np.array([[(f.features[v] - medias[v]) / desvios[v] for v in variables_] for f in filas_train])
    X = sm.add_constant(X, has_constant="add")
    y = np.array([int(f.alza) for f in filas_train])

    modelo = sm.Logit(y, X).fit_regularized(alpha=alpha, L1_wt=0.0, disp=0)

    coeficientes = {v: round(float(c), 4) for v, c in zip(variables_, modelo.params[1:])}
    intercepto = round(float(modelo.params[0]), 4)

    intervalos = {}
    try:
        ic = modelo.conf_int()
        for v, (lo, hi) in zip(variables_, ic[1:]):
            intervalos[v] = (round(float(lo), 4), round(float(hi), 4))
    except Exception:
        pass  # fit_regularized no siempre expone errores estándar; el score sigue siendo válido sin el IC

    return Pesos(tuple(variables_), coeficientes, intercepto, medias, desvios, intervalos, alpha)


def calcular_score(features, pesos):
    """0-100. `features` es un dict como el de extraer_features()."""
    z = pesos.intercepto
    for v in pesos.variables:
        x = (features[v] - pesos.medias[v]) / pesos.desvios[v]
        z += pesos.coeficientes[v] * x
    probabilidad = 1 / (1 + math.exp(-z))
    return round(probabilidad * 100, 1)


@dataclass
class Evaluacion:
    n: int
    exactitud: float
    exactitud_mayoria: float
    auc: float | None


def evaluar(filas_test, pesos, umbral=50.0):
    if not filas_test:
        return Evaluacion(0, 0.0, 0.0, None)
    puntajes = [(calcular_score(f.features, pesos), f.alza) for f in filas_test]
    aciertos = sum(1 for s, alza in puntajes if (s >= umbral) == alza)
    mayoria = max(sum(1 for _, a in puntajes if a), sum(1 for _, a in puntajes if not a))
    auc = _auc([s for s, _ in puntajes], [a for _, a in puntajes])
    return Evaluacion(len(filas_test), round(aciertos / len(filas_test), 3), round(mayoria / len(filas_test), 3), auc)


def _auc(puntajes, etiquetas):
    """Área bajo la curva ROC, calculada como probabilidad de que un caso
    positivo al azar tenga puntaje mayor que uno negativo al azar (equivale
    al estadístico U de Mann-Whitney normalizado) — evita traer sklearn
    solo para esto."""
    positivos = [s for s, e in zip(puntajes, etiquetas) if e]
    negativos = [s for s, e in zip(puntajes, etiquetas) if not e]
    if not positivos or not negativos:
        return None
    mayores = sum((p > n) + 0.5 * (p == n) for p in positivos for n in negativos)
    return round(mayores / (len(positivos) * len(negativos)), 3)
