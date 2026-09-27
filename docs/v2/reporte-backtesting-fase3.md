# Radar 2.0 — backtesting, fase 3

Generado el 2026-09-27 por `python -m pipeline.cli backtest`. Método: `docs/v2/01-definicion-tendencia.md` (aprobado). Código: `pipeline/backtesting.py`, `pipeline/modelos.py`.

Muestra: **36 series** × hasta 5 cortes cada una → **2060 evaluaciones** (serie × corte × horizonte × modelo).

## Puerta de salida: ¿algún modelo le gana al baseline?

"Ganarle" no es "tener un número más alto" — con miles de evaluaciones hasta una diferencia de una fracción de punto sale "mayor" sin significar nada (pasó en la primera corrida real: 0.610 contra 0.605, un solo acierto de diferencia sobre 172 casos). Exige dos cosas sobre los mismos casos emparejados con el baseline: significancia estadística (test binomial exacto de McNemar, p < 0.05) y una diferencia de exactitud de al menos 3 puntos. No se pasa un modelo a producción sin ganarle aquí — si ninguno le gana, el panel se queda con el baseline, y esa también es una respuesta válida.

| Horizonte | media_movil | holt_winters | sarima |
|---|---|---|---|
| 6 meses | no le gana | no le gana | no le gana |
| 12 meses | no le gana | no le gana | no le gana |
| 24 meses | no le gana | le gana ✓ | no le gana |

Se corrieron **9 pruebas** de significancia a la vez (3 modelos × 3 horizontes), con α = 0.05 cada una — eso por sí solo deja una probabilidad real de un positivo falso por puro azar de comparar varias veces. Corrigiendo con Bonferroni (α = 0.05 / 9 ≈ 0.0056):

**El resultado cambia**: 1 combinación(es) parecían ganarle al baseline sin corregir, pero **ninguna sobrevive** la corrección. La conclusión honesta de esta corrida es que, con esta muestra, ningún modelo le gana de verdad al baseline — no se adopta ninguno todavía. Ver `docs/v2/hallazgo-backtesting-fase3.md`.

## Exactitud y error por modelo y horizonte

Exactitud = % de veces que la etiqueta pronosticada coincidió con la real. Error mediano = diferencia absoluta mediana entre el nivel futuro pronosticado y el real (escala propia de cada serie).

La fila `(mayoría)` no es un modelo: es adivinar siempre la etiqueta real más frecuente de ese horizonte, sin mirar la serie — la vara mínima real. 25% (una de cuatro al azar) sería la referencia incorrecta si las clases estuvieran parejas; en la práctica "estable" domina, sobre todo a horizontes largos, así que la vara mínima real es más alta que eso.

| Modelo | Horizonte | n | Exactitud | Error mediano |
|---|---:|---:|---:|---:|
| (mayoría) | 6 | — | 0.718 | — |
| (mayoría) | 12 | — | 0.552 | — |
| (mayoría) | 24 | — | 0.422 | — |
| naive_estacional | 6 | 170 | 0.782 | 2.34 |
| naive_estacional | 12 | 172 | 0.605 | 4.83 |
| naive_estacional | 24 | 173 | 0.439 | 7.66 |
| media_movil | 6 | 170 | 0.759 | 2.14 |
| media_movil | 12 | 172 | 0.547 | 4.83 |
| media_movil | 24 | 173 | 0.422 | 7.66 |
| holt_winters | 6 | 170 | 0.818 | 2.13 |
| holt_winters | 12 | 172 | 0.57 | 3.79 |
| holt_winters | 24 | 173 | 0.52 | 8.04 |
| sarima | 6 | 170 | 0.818 | 1.73 |
| sarima | 12 | 172 | 0.61 | 4.14 |
| sarima | 24 | 173 | 0.503 | 7.18 |