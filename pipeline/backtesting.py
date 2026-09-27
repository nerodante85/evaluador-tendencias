"""Backtesting de Radar 2.0.

La pregunta que responde: parado en un momento del pasado, viendo solo lo
que se sabía hasta ahí, ¿el pronóstico de cada modelo habría acertado la
etiqueta que la serie tuvo en realidad `horizonte` meses después?

Reutiliza `pipeline.senales.etiquetar()` sin duplicarlo: la etiqueta
"predicha" sale de correr la MISMA regla sobre una serie donde el tramo
futuro no es el dato real sino el pronóstico del modelo. Esto es posible
porque `etiquetar()` no le importa de dónde salieron los números — solo
mira índices dentro de la lista que se le pasa.

No se elige un modelo porque sea más sofisticado. `comparar_contra_baseline`
decide, horizonte por horizonte, si un modelo le gana de verdad al naive
estacional — esa es la puerta de salida de la fase 3 (docs/v2/plan.md).
"""

import random
from dataclasses import dataclass, field

from .modelos import MODELOS
from .modelos import media_movil as _media_movil_de_respaldo
from .senales import etiquetar

HORIZONTES = (6, 12, 24)
MESES_MAX = max(HORIZONTES)
MINIMO_HISTORIA_PARA_CORTE = 36  # meses de "calentamiento" dentro de la historia útil antes del primer corte
ETIQUETAS_EVALUABLES = ("alza_sostenida", "baja_sostenida", "pico_atencion", "estable")


@dataclass(frozen=True)
class Resultado:
    mercado: str
    nodo: str
    corte: int
    horizonte: int
    modelo: str
    etiqueta_real: str
    etiqueta_pred: str
    futuro_real: float | None
    futuro_pred: float | None

    @property
    def acierto(self):
        return self.etiqueta_real == self.etiqueta_pred

    @property
    def error_futuro(self):
        if self.futuro_real is None or self.futuro_pred is None:
            return None
        return abs(self.futuro_real - self.futuro_pred)


def cortes_de_prueba(n, inicio_util, n_cortes, meses_max=MESES_MAX, calentamiento=MINIMO_HISTORIA_PARA_CORTE):
    """`n_cortes` puntos espaciados dentro de la zona evaluable: después del
    calentamiento (para no ajustar modelos sobre ruido de bajo volumen) y
    con margen suficiente al final para que el horizonte más largo cabalgue
    dentro de la serie real (si no, no hay futuro real con qué comparar)."""
    inicio = (inicio_util or 0) + calentamiento - 1
    fin = n - 1 - meses_max
    if fin <= inicio or n_cortes <= 0:
        return []
    if n_cortes == 1:
        return [fin]
    paso = (fin - inicio) / (n_cortes - 1)
    cortes = sorted({round(inicio + paso * i) for i in range(n_cortes)})
    return [c for c in cortes if inicio <= c <= fin]


def evaluar_serie(valores, cortes, modelos=MODELOS, horizontes=HORIZONTES):
    """Corre todos los `modelos` en cada uno de los `cortes` de una serie.
    Cada modelo se ajusta UNA vez por corte (pronosticando el horizonte más
    largo) y el pronóstico se recorta para los horizontes más cortos — no
    tiene sentido reajustar el mismo modelo tres veces por corte."""
    meses_max = max(horizontes) if horizontes else 0
    filas = []
    for corte in cortes:
        conocida = valores[: corte + 1]
        for nombre, modelo in modelos.items():
            try:
                pronostico = list(modelo(conocida, meses_max))
            except Exception:
                # Respaldo fijo, no el de `modelos`: si alguien corre el
                # backtesting con un subconjunto que no incluye media_movil
                # (una prueba, un experimento puntual), el respaldo no debe
                # depender de que esté ahí también.
                pronostico = list(_media_movil_de_respaldo(conocida, meses_max))
            extendida = conocida + pronostico
            for h in horizontes:
                e_real = etiquetar(valores, corte, h)
                if e_real.etiqueta not in ETIQUETAS_EVALUABLES:
                    continue  # sin futuro real evaluable en este corte (no debería pasar si cortes() se usó bien)
                e_pred = etiquetar(extendida, corte, h)
                filas.append(
                    Resultado(
                        mercado="", nodo="", corte=corte, horizonte=h, modelo=nombre,
                        etiqueta_real=e_real.etiqueta, etiqueta_pred=e_pred.etiqueta,
                        futuro_real=e_real.futuro, futuro_pred=e_pred.futuro,
                    )
                )
    return filas


def muestra_estratificada(tax, calidad, n, clases=("apta_backtest",), semilla=42):
    """`n` pares (mercado, nodo_id) repartidos por tipo de nodo, para que la
    muestra no quede dominada por "prenda" (la categoría con más series
    aptas) a costa de dejar afuera "estilo" o "estampado"."""
    candidatos = {}
    for mercado in tax.mercados:
        for nodo_id, nodo in tax.nodos.items():
            if calidad.get((mercado, nodo_id), {}).get("clase") in clases:
                candidatos.setdefault(nodo.tipo, []).append((mercado, nodo_id))

    rng = random.Random(semilla)
    for grupo in candidatos.values():
        rng.shuffle(grupo)

    tipos = sorted(candidatos)
    elegidos, i = [], 0
    while len(elegidos) < n and tipos:
        tipo = tipos[i % len(tipos)]
        if candidatos[tipo]:
            elegidos.append(candidatos[tipo].pop())
        else:
            tipos.remove(tipo)
            i -= 1
        i += 1
    return elegidos


def correr(tax, calidad, dir_raw, leer_serie, ruta_serie, n_series=36, n_cortes=5, modelos=MODELOS, horizontes=HORIZONTES, log=print):
    """Backtesting completo sobre una muestra. `leer_serie`/`ruta_serie` se
    inyectan (en vez de importar pipeline.historia acá) para que las pruebas
    puedan pasar dobles sin tocar disco."""
    from .calidad import inicio_historia_util

    muestra = muestra_estratificada(tax, calidad, n_series)
    resultados = []
    for i, (mercado, nodo_id) in enumerate(muestra, 1):
        reg = leer_serie(ruta_serie(mercado, nodo_id, dir_raw))
        valores = [v for _, v in reg["serie"]]
        inicio_util = inicio_historia_util(valores)
        cortes = cortes_de_prueba(len(valores), inicio_util, n_cortes)
        filas = evaluar_serie(valores, cortes, modelos, horizontes)
        for f in filas:
            resultados.append(
                Resultado(mercado, nodo_id, f.corte, f.horizonte, f.modelo, f.etiqueta_real, f.etiqueta_pred, f.futuro_real, f.futuro_pred)
            )
        log(f"[{i}/{len(muestra)}] {mercado} {nodo_id}: {len(cortes)} corte(s), {len(filas)} fila(s)")
    return resultados


@dataclass
class Metricas:
    n: int = 0
    aciertos: int = 0
    errores: list = field(default_factory=list)

    @property
    def exactitud(self):
        return round(self.aciertos / self.n, 3) if self.n else None

    @property
    def error_mediano(self):
        if not self.errores:
            return None
        s = sorted(self.errores)
        m = len(s) // 2
        return round(s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2, 2)


def frecuencia_clase_mayoritaria(resultados, horizontes=HORIZONTES):
    """Qué tan bien le iría a la estrategia más tonta posible: adivinar
    siempre la etiqueta real más frecuente de ese horizonte, sin mirar la
    serie. No es un modelo — es la vara mínima real para decir que un
    modelo "aprendió" algo. 25% (una de cuatro etiquetas al azar) es la
    referencia equivocada si las clases no están parejas, y en la práctica
    no lo están: "estable" domina, sobre todo a horizontes largos."""
    from collections import Counter

    por_horizonte = {}
    for h in horizontes:
        vistos = {}
        for r in resultados:
            if r.horizonte == h:
                vistos[(r.mercado, r.nodo, r.corte)] = r.etiqueta_real
        if not vistos:
            continue
        conteo = Counter(vistos.values())
        por_horizonte[h] = max(conteo.values()) / len(vistos)
    return por_horizonte


def agregar_por_modelo_y_horizonte(resultados):
    """{(modelo, horizonte): Metricas}."""
    agregado = {}
    for r in resultados:
        m = agregado.setdefault((r.modelo, r.horizonte), Metricas())
        m.n += 1
        m.aciertos += int(r.acierto)
        if r.error_futuro is not None:
            m.errores.append(r.error_futuro)
    return agregado


def emparejar_con_baseline(resultados, baseline="naive_estacional"):
    """Para cada horizonte y cada modelo que no sea el baseline, empareja el
    resultado con el del baseline EN EL MISMO (mercado, nodo, corte) — la
    comparación tiene que ser sobre el mismo caso, no sobre promedios
    sueltos. Devuelve {(modelo, horizonte): [(acierto_baseline, acierto_modelo), ...]}."""
    por_clave = {(r.mercado, r.nodo, r.corte, r.horizonte, r.modelo): r for r in resultados}
    pares = {}
    for r in resultados:
        if r.modelo == baseline:
            continue
        rb = por_clave.get((r.mercado, r.nodo, r.corte, r.horizonte, baseline))
        if rb is None:
            continue
        pares.setdefault((r.modelo, r.horizonte), []).append((rb.acierto, r.acierto))
    return pares


def matriz_confusion_por_clase(resultados, horizontes=HORIZONTES, clases=ETIQUETAS_EVALUABLES):
    """{(modelo, horizonte): {clase: {"tp", "fp", "fn"}}} — la exactitud agregada
    (arriba) puede esconder que un modelo falle sistemáticamente más en una
    dirección que en otra, sobre todo con clases desbalanceadas (`estable`
    domina la mayoría de los horizontes). Base para `precision_recall_por_clase`."""
    conteo = {}
    for r in resultados:
        clave = (r.modelo, r.horizonte)
        m = conteo.setdefault(clave, {c: {"tp": 0, "fp": 0, "fn": 0} for c in clases})
        if r.etiqueta_pred == r.etiqueta_real:
            if r.etiqueta_real in m:
                m[r.etiqueta_real]["tp"] += 1
        else:
            if r.etiqueta_pred in m:
                m[r.etiqueta_pred]["fp"] += 1
            if r.etiqueta_real in m:
                m[r.etiqueta_real]["fn"] += 1
    return conteo


def precision_recall_por_clase(resultados, horizontes=HORIZONTES, clases=ETIQUETAS_EVALUABLES):
    """{(modelo, horizonte): {clase: {"precision", "recall", "tp", "fp", "fn"}}}.

    Precision: de las veces que el modelo dijo `clase`, ¿cuántas eran ciertas?
    (falso positivo caro: comprar por una señal que "predijo" alza y no era).
    Recall: de las veces que la serie SÍ terminó en `clase`, ¿cuántas detectó
    el modelo? (falso negativo caro: dejar pasar una tendencia real que el
    modelo no marcó). `None` cuando no hay denominador (el modelo nunca
    predijo esa clase, o esa clase nunca ocurrió en la muestra)."""
    matriz = matriz_confusion_por_clase(resultados, horizontes, clases)
    salida = {}
    for clave, por_clase in matriz.items():
        salida[clave] = {}
        for c, m in por_clase.items():
            precision = round(m["tp"] / (m["tp"] + m["fp"]), 3) if (m["tp"] + m["fp"]) > 0 else None
            recall = round(m["tp"] / (m["tp"] + m["fn"]), 3) if (m["tp"] + m["fn"]) > 0 else None
            salida[clave][c] = {"precision": precision, "recall": recall, **m}
    return salida


def comparar_contra_baseline(resultados, horizontes=HORIZONTES, baseline="naive_estacional", modelos=MODELOS, alpha=0.05, margen_minimo=0.03):
    """Para cada (modelo, horizonte) que no sea el baseline: ¿le ganó de
    verdad, o solo parece mejor por azar de la muestra?

    Con miles de evaluaciones, hasta una diferencia de exactitud de una
    fracción de punto puede salir "mayor" sin significar nada — pasó en la
    primera corrida real (sarima 0.610 vs. naive 0.605 a 12 meses: un solo
    acierto de diferencia sobre 172 casos). Por eso "ganar" exige DOS cosas:

    1. Significancia estadística sobre los casos EMPAREJADOS (test binomial
       exacto de McNemar: de los casos donde acierta uno de los dos y el
       otro no, ¿el modelo acierta más seguido que el baseline, de una
       forma que no se explique por azar?).
    2. Un margen mínimo de exactitud (`margen_minimo`): significativo no es
       lo mismo que relevante para el negocio.

    El error del nivel pronosticado (mediana) se reporta aparte, pero ya no
    decide el veredicto: dos modelos pueden acertar la MISMA etiqueta con
    niveles distintos, y forzar ahí un empate arbitrario (5%) era más
    arbitrario que la propia significancia estadística."""
    from scipy.stats import binomtest

    pares = emparejar_con_baseline(resultados, baseline)
    veredicto = {}
    for h in horizontes:
        for nombre in modelos:
            if nombre == baseline:
                continue
            lista = pares.get((nombre, h), [])
            n = len(lista)
            if n == 0:
                continue
            acierto_base = sum(b for b, _ in lista) / n
            acierto_modelo = sum(m for _, m in lista) / n
            solo_acierta_base = sum(1 for b, m in lista if b and not m)
            solo_acierta_modelo = sum(1 for b, m in lista if not b and m)
            discordantes = solo_acierta_base + solo_acierta_modelo
            if discordantes == 0:
                veredicto[(nombre, h)] = False
                continue
            p_valor = binomtest(solo_acierta_modelo, discordantes, 0.5, alternative="greater").pvalue
            margen = acierto_modelo - acierto_base
            veredicto[(nombre, h)] = bool(p_valor < alpha and margen >= margen_minimo)
    return veredicto
