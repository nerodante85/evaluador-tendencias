# Radar 2.0 — Trend Score, fase 4

Generado el 2026-09-27 por `python -m pipeline.cli trend_score`. Pesos calibrados con regresión logística regularizada (L2) sobre `pipeline/senales.py` y la misma infraestructura de `pipeline/backtesting.py` (fase 3).

**Horizonte: 24 meses** — el único donde la fase 3 demostró que hay señal real que capturar (holt_winters/sarima le ganan al baseline ahí). El target es binario: ¿la serie terminó en `alza_sostenida` a ese horizonte?

Entrenamiento: 1784 filas (series distintas de las de prueba). Prueba: 753 filas, de series que el ajuste nunca vio.

## Puerta de salida: ¿el score predice mejor que adivinar la clase mayoritaria?

- Exactitud fuera de muestra (score ≥ 50 = "probable alza"): **0.639**
- Adivinar siempre la clase más común, en el mismo conjunto de prueba: **0.625**
- AUC (¿qué tan seguido un caso que sí fue alza recibe más puntaje que uno que no?, 0.5 = igual que azar): **0.655**

El score generaliza mejor que la referencia mínima en datos que no vio durante el ajuste.

## Pesos (sobre variables estandarizadas — comparables entre sí)

Positivo = sube el score; negativo = lo baja. El intervalo es al 95%; si cruza el cero, esa variable no aporta con la evidencia actual (no se descarta del score por eso — es información, se reporta tal cual).

**Antes de leer esta tabla como "por qué" de una señal, ver `docs/v2/hallazgo-trend-score-fase4.md`**: dos pesos salen con el signo contrario al que asumía el brief original, y uno de los dos casos es un efecto de colinealidad entre variables, no un hallazgo real — se investigó cada uno por separado.

| Variable | Peso | Intervalo 95% |
|---|---:|---|
| crecimiento | -0.0278 | [-0.1991, 0.1434] |
| aceleracion | -0.0997 | [-0.2226, 0.0233] |
| persistencia | 0.4582 | [0.3085, 0.6079] |
| volatilidad | 0.2168 | [0.083, 0.3507] |
| saturacion | 0.1073 | [-0.0234, 0.2381] |
| (intercepto) | -0.6101 | — |

## Limitaciones, para no sobrevender esto

- El tamaño de muestra es el mismo problema de la fase 3: con más series y cortes el intervalo de los pesos se va a angostar. Antes de subir esto a producción vale la pena repetir con una muestra mayor, igual que se hizo en el backtesting.
- El score se calibró contra `alza_sostenida` únicamente. No distingue "buen momento para vender/liquidar" (`baja_sostenida`) de "nada está pasando" (`estable`) — para eso hoy sigue sirviendo la etiqueta del motor de señales (fase 2), no este número.
- La estacionalidad NO entra al puntaje (una señal estacional no es mejor ni peor) — se reporta aparte y el panel (fase 5) debe mostrarla como advertencia junto al score, no mezclarla.