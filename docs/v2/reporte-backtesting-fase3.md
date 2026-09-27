# Radar 2.0 — backtesting, fase 3

Generado el 2026-09-27 por `python -m pipeline.cli backtest`. Método: `docs/v2/01-definicion-tendencia.md` (aprobado). Código: `pipeline/backtesting.py`, `pipeline/modelos.py`.

Muestra: **280 series** × hasta 10 cortes cada una → **32188 evaluaciones** (serie × corte × horizonte × modelo).

## Puerta de salida: ¿algún modelo le gana al baseline?

"Ganarle" no es "tener un número más alto" — con miles de evaluaciones hasta una diferencia de una fracción de punto sale "mayor" sin significar nada (pasó en la primera corrida real: 0.610 contra 0.605, un solo acierto de diferencia sobre 172 casos). Exige dos cosas sobre los mismos casos emparejados con el baseline: significancia estadística (test binomial exacto de McNemar, p < 0.05) y una diferencia de exactitud de al menos 3 puntos. No se pasa un modelo a producción sin ganarle aquí — si ninguno le gana, el panel se queda con el baseline, y esa también es una respuesta válida.

| Horizonte | media_movil | holt_winters | sarima |
|---|---|---|---|
| 6 meses | no le gana | no le gana | no le gana |
| 12 meses | no le gana | no le gana | no le gana |
| 24 meses | no le gana | le gana ✓ | le gana ✓ |

Se corrieron **9 pruebas** de significancia a la vez (3 modelos × 3 horizontes), con α = 0.05 cada una — eso por sí solo deja una probabilidad real de un positivo falso por puro azar de comparar varias veces. Corrigiendo con Bonferroni (α = 0.05 / 9 ≈ 0.0056):

**2 combinación(es) sobreviven** incluso con la corrección: holt_winters a 24 meses, sarima a 24 meses.

## Exactitud y error por modelo y horizonte

Exactitud = % de veces que la etiqueta pronosticada coincidió con la real. Error mediano = diferencia absoluta mediana entre el nivel futuro pronosticado y el real (escala propia de cada serie).

La fila `(mayoría)` no es un modelo: es adivinar siempre la etiqueta real más frecuente de ese horizonte, sin mirar la serie — la vara mínima real. 25% (una de cuatro al azar) sería la referencia incorrecta si las clases estuvieran parejas; en la práctica "estable" domina, sobre todo a horizontes largos, así que la vara mínima real es más alta que eso.

| Modelo | Horizonte | n | Exactitud | Error mediano |
|---|---:|---:|---:|---:|
| (mayoría) | 6 | — | 0.765 | — |
| (mayoría) | 12 | — | 0.608 | — |
| (mayoría) | 24 | — | 0.427 | — |
| naive_estacional | 6 | 2656 | 0.848 | 2.25 |
| naive_estacional | 12 | 2681 | 0.656 | 3.92 |
| naive_estacional | 24 | 2710 | 0.461 | 7.5 |
| media_movil | 6 | 2656 | 0.779 | 2.2 |
| media_movil | 12 | 2681 | 0.601 | 3.92 |
| media_movil | 24 | 2710 | 0.42 | 7.5 |
| holt_winters | 6 | 2656 | 0.844 | 1.62 |
| holt_winters | 12 | 2681 | 0.657 | 3.38 |
| holt_winters | 24 | 2710 | 0.551 | 6.53 |
| sarima | 6 | 2656 | 0.85 | 1.53 |
| sarima | 12 | 2681 | 0.672 | 3.26 |
| sarima | 24 | 2710 | 0.543 | 6.71 |

## Precision y recall de "alza_sostenida" — la clase que más importa para decidir compra

La exactitud de arriba es un promedio sobre las cuatro etiquetas; con clases desbalanceadas (`estable` domina casi todos los horizontes) puede esconder que un modelo falle sistemáticamente más en una dirección. Estas dos preguntas son distintas y le importan a decisiones distintas:

- **Precision** — de las veces que el modelo dijo "esto va a ser alza sostenida", ¿cuántas eran ciertas? Precision baja = comprar por señales falsas (falso positivo).
- **Recall** — de las veces que la serie SÍ terminó en alza sostenida, ¿cuántas detectó el modelo? Recall bajo = dejar pasar tendencias reales (falso negativo).

| Modelo | Horizonte | Precision | Recall | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| naive_estacional | 6 | — | 0.0 | 0 | 0 | 148 |
| naive_estacional | 12 | — | 0.0 | 0 | 0 | 578 |
| naive_estacional | 24 | — | 0.0 | 0 | 0 | 1046 |
| media_movil | 6 | — | 0.0 | 0 | 0 | 148 |
| media_movil | 12 | — | 0.0 | 0 | 0 | 578 |
| media_movil | 24 | — | 0.0 | 0 | 0 | 1046 |
| holt_winters | 6 | 0.49 | 0.331 | 49 | 51 | 99 |
| holt_winters | 12 | 0.487 | 0.318 | 184 | 194 | 394 |
| holt_winters | 24 | 0.589 | 0.494 | 517 | 361 | 529 |
| sarima | 6 | 0.391 | 0.23 | 34 | 53 | 114 |
| sarima | 12 | 0.528 | 0.279 | 161 | 144 | 417 |
| sarima | 24 | 0.564 | 0.507 | 530 | 409 | 516 |

La matriz completa (las cuatro etiquetas, no solo `alza_sostenida`) queda en `data/v2/backtesting.json` bajo `precision_recall`.