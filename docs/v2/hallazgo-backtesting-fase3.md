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

## Actualización: con más muestra, la sospecha era correcta

Se repitió la misma corrida con una muestra mayor (150 series × 10 cortes, 17.056 evaluaciones en vez de 2.060). La sospecha del final de este documento se confirmó:

| Horizonte | Adivinar siempre "estable" | naive_estacional | holt_winters | sarima |
|---|---:|---:|---:|---:|
| 6 meses | 74.0% | 81.6% | 81.5% | 81.7% |
| 12 meses | 59.1% | 62.9% | 62.7% | 64.3% |
| 24 meses | 42.0% | 43.7% | **53.2%** ✓ | **52.1%** ✓ |

**A 24 meses, tanto Holt-Winters como SARIMA le ganan al baseline de verdad** — significativo por McNemar y sobrevive la corrección de Bonferroni por las 9 pruebas corridas a la vez. A 6 y 12 meses, sigue sin haber ganador: `naive_estacional` sigue siendo difícil de superar en esos horizontes, y no hay razón para complicar el panel ahí.

Esto no contradice el punto anterior sobre no forzar una conclusión — es lo contrario: la conclusión cambió porque se corrigió la causa real (tamaño de muestra), no porque se haya bajado el umbral de significancia ni quitado la corrección de Bonferroni. Mismo método, misma vara, más evidencia.

**Recomendación concreta para la fase 4:** usar `naive_estacional` a 6 y 12 meses (nada le gana, y es el más simple y explicable), y `holt_winters` a 24 meses (le gana al baseline por ~9.5 puntos, con el error de nivel más bajo de los cuatro en ese horizonte). No se comparó Holt-Winters contra SARIMA directamente entre sí — solo cada uno contra el baseline —, así que entre los dos, Holt-Winters es la elección algo más simple y con métricas marginalmente mejores, pero SARIMA queda como candidato razonable si en el futuro se combinan modelos.

## Qué significa para las fases que siguen

- **Fase 4 (Trend Score):** con la corrida grande (ver "Actualización" arriba), la recomendación por horizonte queda: `naive_estacional` a 6 y 12 meses, `holt_winters` a 24 meses — el único caso donde un modelo más complejo demostró, con significancia real, que valía la pena.
- **Fase 5 (panel):** la "confianza estadística" que se le muestre al usuario debe reflejar esto — a 24 meses, incluso ganándole al baseline, el mejor modelo (53.2%) sigue lejos de la certeza. Prometer certeza a ese horizonte sería deshonesto con la propia evidencia que este backtesting generó.
