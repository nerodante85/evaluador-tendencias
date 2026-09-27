# Hallazgo (auditoría 2026-09-27): el baseline que "gana" a 6 y 12 meses nunca detecta una alza sostenida real

Este hallazgo salió de agregar precision/recall por clase al backtesting (H-04/sección 8 de `docs/auditoria-2026-09-27-prelanzamiento/AUDIT-REPORT.md`) y de repetir la corrida con muestra grande (280 series × 10 cortes, 32.188 evaluaciones — `data/v2/backtesting.json`, `docs/v2/reporte-backtesting-fase3.md`).

## El número que lo cambia todo

| Modelo | Horizonte | Recall de `alza_sostenida` |
|---|---:|---:|
| naive_estacional | 6 meses | **0.0** (0 de 148 casos reales detectados) |
| naive_estacional | 12 meses | **0.0** (0 de 578 casos reales detectados) |
| naive_estacional | 24 meses | **0.0** (0 de 1046 casos reales detectados) |
| media_movil | los tres horizontes | **0.0**, igual que naive |
| holt_winters | 24 meses | 0.494 |
| sarima | 24 meses | 0.507 |

`naive_estacional` y `media_movil` **nunca, ni una sola vez en 32.188 evaluaciones, predijeron `alza_sostenida`.** No es una tasa baja — es cero. Tiene una explicación mecánica simple: `naive_estacional` repite el mismo mes del año anterior; `media_movil` proyecta plano el promedio de los últimos 12 meses. Ninguno de los dos puede, por construcción, generar un pronóstico que crezca más allá de lo que ya pasó — así que nunca cumplen el umbral de `crecimiento ≥ 25%` que exige la etiqueta `alza_sostenida` (`docs/v2/01-definicion-tendencia.md`). No es un defecto de esta corrida: es lo que un modelo sin componente de tendencia hace siempre.

## Por qué esto no se veía con exactitud sola

La "puerta de salida" de la fase 3 (`comparar_contra_baseline`, McNemar + Bonferroni) usa **exactitud agregada** sobre las cuatro etiquetas. A 6 y 12 meses, `estable` es la clase mayoritaria (76.5% y 60.8% de los casos) — un modelo que casi siempre predice algo parecido a "no cambió mucho" acierta seguido **sin necesitar detectar ni una sola alza real**. Por eso `naive_estacional` "gana" (o empata) en exactitud a esos horizontes (84.8% y 65.6%) y el veredicto oficial de la fase 3 dice, correctamente pero de forma incompleta, que "ningún modelo le gana al baseline a 6 y 12 meses — se sigue con naive_estacional". Esa frase es cierta para la exactitud agregada y **engañosa** para la pregunta que de verdad le importa a un empresario: ¿esto detecta una tendencia real cuando aparece?

## Qué significa esto para el producto, con precisión

**El panel público (Radar 2.0) no está afectado hoy, y hay que decirlo con la misma claridad que el problema:** el Trend Score (`pipeline/trend_score.py`) se calibró **únicamente a 24 meses**, exactamente porque la fase 3 ya había mostrado que ese es el único horizonte con señal real (`docs/v2/hallazgo-trend-score-fase4.md`). El panel nunca expuso una recomendación basada en el "baseline ganador" de 6 o 12 meses — esa decisión, tomada antes de este hallazgo, resultó ser la correcta por razones que en ese momento no se habían visto tan claras.

**Lo que sí queda expuesto es un hueco real en la metodología de la "puerta de salida" misma:** `comparar_contra_baseline()` solo mira exactitud + significancia estadística, nunca precision/recall por clase. Si en el futuro alguien decide extender el Trend Score (o cualquier recomendación accionable) a 6 o 12 meses usando el mismo criterio de "¿le gana al baseline en exactitud?", **el resultado sería adoptar en silencio un modelo con recall cero para la clase que justifica una compra.**

## Qué hacer con esto

No se cambia el código de `pipeline/backtesting.py` en esta auditoría (la función `comparar_contra_baseline` ya calcula lo necesario — `precision_recall_por_clase` corre en paralelo, no reemplaza nada). Se deja como recomendación de proceso, para cuando se revise la metodología después del 9 de noviembre:

1. **Cualquier futura "puerta de salida" para un horizonte nuevo debe exigir recall mínimo de `alza_sostenida` (y de `baja_sostenida`), no solo exactitud agregada y significancia.** Un modelo con 0% de recall en la clase que importa no debería poder "ganar" solo por acertar mucho en la clase que no importa.
2. Confirma, con evidencia adicional y más fuerte que antes, que **calibrar el Trend Score solo a 24 meses fue la decisión correcta** — no hay ningún horizonte más corto donde valga la pena confiar en un pronóstico de tendencia hoy.
3. Si alguna vez se agregan más modelos o más horizontes, este informe (`docs/v2/reporte-backtesting-fase3.md`) ya reporta precision/recall por clase automáticamente — no hace falta reconstruir este análisis a mano.

## Números completos

Ver la sección "Precision y recall de 'alza_sostenida'" en `docs/v2/reporte-backtesting-fase3.md` (las cuatro etiquetas completas están en `data/v2/backtesting.json`, campo `precision_recall`).
