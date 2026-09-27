# Hallazgo de la fase 3: con esta muestra, ningún modelo le gana al baseline

Corrida real: 36 series (repartidas por tipo de nodo) × 5 cortes cada una × 3 horizontes (6, 12, 24 meses) × 4 modelos (naive estacional, media móvil, Holt-Winters, SARIMA) = 2060 evaluaciones.

## La comparación ingenua mentía

La primera versión de `comparar_contra_baseline()` decidía "le gana" con solo mirar si la exactitud de un modelo era mayor que la del baseline. Con esa regla, SARIMA "le ganaba" al baseline a 12 meses: 0.610 contra 0.605. Sobre 172 casos, eso es **un acierto de diferencia**. No es evidencia de nada — es la clase de ruido que aparece incluso si los dos modelos fueran idénticos.

Se reemplazó por un test binomial exacto pareado (McNemar): de los casos donde uno de los dos acierta y el otro no, ¿el modelo gana esos empates más seguido de lo que el azar explicaría? Además se exige un margen mínimo de 3 puntos de exactitud — significativo no es lo mismo que relevante.

## Con esa corrección, casi todo deja de "ganar" — y lo poco que queda tampoco sobrevive

De las 9 combinaciones modelo × horizonte, solo una (`holt_winters` a 24 meses) pasó el test de significancia sin corregir. Pero se corrieron **9 pruebas a la vez**, y con α = 0.05 cada una eso deja una probabilidad real de encontrar "algo significativo" por puro azar de comparar varias veces (el problema clásico de comparaciones múltiples). Corrigiendo con Bonferroni (α = 0.05/9 ≈ 0.0056), esa única victoria **tampoco sobrevive**.

**Conclusión honesta: con esta muestra, ningún modelo de los cuatro le gana de verdad al naive estacional.**

## Esto no es un fracaso de la fase 3 — es lo que el backtesting existe para decir

El brief original de esta v2 fue explícito: "no elijas un modelo porque sea más sofisticado, sino porque demuestra mejores resultados en backtesting." Aquí el backtesting dice que, hoy, con 36 series y 5 cortes, ninguno lo demuestra. Forzar una conclusión distinta —bajar el umbral de significancia, quitar la corrección de Bonferroni, elegir otra muestra hasta que algo "gane"— sería exactamente la trampa que este proyecto ha evitado desde la fase 0 (calibrar el método para que confirme lo que ya se quería creer).

## La vara mínima real no es 25% — y algún modelo no la pasa ni por eso

Un primer borrador de este documento comparaba contra "adivinar al azar entre 4 etiquetas" (25%). Esa referencia está mal: las etiquetas no están parejas. Se agregó `frecuencia_clase_mayoritaria()` — adivinar siempre "estable" (la más común) sin mirar la serie — como la vara mínima de verdad:

| Horizonte | Adivinar siempre "estable" | naive_estacional | El mejor modelo |
|---|---:|---:|---:|
| 6 meses | 71.8% | 78.2% | 81.8% (Holt-Winters / SARIMA) |
| 12 meses | 55.2% | 60.5% | 61.0% (SARIMA) |
| 24 meses | 42.2% | 43.9% | 52.0% (Holt-Winters) |

**`media_movil` a 24 meses (42.2%) queda literalmente empatado con adivinar siempre "estable"** — no aporta nada frente a la estrategia más floja posible. `naive_estacional` le gana por apenas 1.7 puntos. Ningún modelo, ni siquiera el baseline, está lejos de la vara mínima a ese horizonte.

Lo que sí es un hallazgo real y accionable:

- **El baseline (naive estacional) es sorprendentemente competitivo, pero menos de lo que parecía antes de tener la vara correcta.** A 6 meses su 78.2% suena bien hasta que se ve que adivinar siempre "estable" ya daba 71.8% — la ganancia real de "mirar el mismo mes del año pasado" es de 6-7 puntos, no de 53.
- **La exactitud cae con el horizonte para TODOS los modelos, y se acerca a la vara mínima** (de +6-10 puntos sobre "siempre estable" a 6 meses, a +0-10 puntos a 24 meses). Es la base para que el panel (fase 5) anuncie con qué horizonte conviene hablar con confianza, categoría por categoría, en vez de prometer 24 meses parejo para todo.
- **El tamaño de la muestra es la sospecha más probable, no los modelos en sí.** 36 series × 5 cortes = 180 puntos de comparación por horizonte reparte poca potencia estadística entre 9 pruebas. Antes de descartar Holt-Winters y SARIMA, vale la pena repetir esta misma corrida con una muestra más grande (más series, más cortes) — el código ya lo soporta (`python -m pipeline.cli backtest --series 150 --cortes 10`), solo toma más tiempo de cómputo.

## Qué significa para las fases que siguen

- **Fase 4 (Trend Score):** por ahora, el score debería construirse sobre el naive estacional o descartar por completo la idea de "elegir un modelo ganador" en favor de usar el propio motor de señales de la fase 2 (que no pronostica, solo describe el estado actual) como la base más defendible. No hay evidencia todavía para justificar la complejidad de un SARIMA en producción.
- **Fase 5 (panel):** la "confianza estadística" que se le muestre al usuario debe reflejar esto — a 24 meses hasta el mejor modelo queda a menos de 10 puntos de "adivinar siempre estable". Prometer certeza a ese horizonte sería deshonesto con la propia evidencia que este backtesting generó.
- **Repetir con más muestra** es la acción concreta pendiente, no un ajuste de umbrales.
