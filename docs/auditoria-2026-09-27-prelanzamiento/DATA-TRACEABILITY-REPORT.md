# Trazabilidad de datos — casos reconstruidos

Regla del brief de auditoría: cada pronóstico importante debe poder reconstruirse como
**Fuente → dato → período → región → señal → metodología → modelo → cálculo → pronóstico → incertidumbre.**

Se reconstruyeron dos casos reales, verificados contra archivos concretos del repositorio (no inferidos).

---

## Caso 1 — Radar 2.0: "Azul marino", Colombia (visto en vivo el 2026-09-27)

| Eslabón | Valor | Evidencia |
|---|---|---|
| Fuente | Google Trends, vía `pytrends` (no oficial) | `pipeline/fuentes/trends.py` |
| Dato | Serie mensual de interés de búsqueda para la consulta configurada | `data/v2/raw/trends/CO/color.azul_marino.json` |
| Consulta exacta | `azul marino` (mercado CO) | `taxonomia/colores.yaml:16`, expuesta también en el catálogo (`m.query`) |
| Período | `timeframe="all"` (2004–fecha de descarga) | `pipeline/fuentes/trends.py:14` |
| Región | Colombia (`geo=CO`), dentro de la categoría "Ropa" de Trends salvo override | `taxonomia.py::Nodo.categoria` |
| Señal | `estado_actual` a horizonte 12 meses, ventana 12 meses | `pipeline/senales.py::estado_actual` |
| Metodología | `docs/v2/01-definicion-tendencia.md` (aprobada por Ricardo, 2026-09-27, sin cambios) | citado en `senales.py:9` |
| Modelo (si aplica score) | Regresión logística L2, calibrada a horizonte 24 meses sobre 5 variables estandarizadas | `pipeline/trend_score.py` |
| Cálculo | `crecimiento`, `persistencia`, `aceleración`, `volatilidad`, `saturación` calculados desde la serie truncada a "hoy", estandarizados con las medias/desvíos del entrenamiento, combinados con los coeficientes de `trend_score_pesos.json` | `trend_score.py::calcular_score` |
| Pronóstico | Score = 48.5/100, etiqueta "alza_sostenida" | Verificado en vivo en `v2.html` |
| Incertidumbre | AUC 0.675 fuera de muestra, comunicado en la tarjeta expandida ("acierta el 68% de las veces mejor que el azar") | `DashboardV2.jsx:122` |

**Conclusión del caso:** la cadena completa es reconstruible de punta a punta con evidencia verificable en archivos concretos. Este es el estándar que debería sostener cualquier afirmación comercial sobre Radar 2.0.

**Matiz importante:** "alza_sostenida" aquí describe la ventana que terminó hace ~12 meses (la ventana "futura" de `estado_actual`, que ya es historia), no una predicción de los próximos 12 meses. El score de 48.5 sí es prospectivo (a 24 meses desde hoy). Estos son dos números con significados temporales distintos mostrados en la misma tarjeta — ver H-09 en `AUDIT-REPORT.md`.

---

## Caso 2 — v1: señal #10 "Poetcore", corroborada por Pinterest

| Eslabón | Valor | Evidencia |
|---|---|---|
| Fuente | Google Trends (`pytrends`) + Pinterest Predicts (editorial, anual) | `fetch_trends.py`, `src/data/contexto.json` |
| Dato | Serie de 24 meses de interés de búsqueda | `src/data/trends.json` (generado, no se lee directo del repo por convención de `CLAUDE.md`) |
| Consulta | La configurada en `trends_config.json` para la señal id 10 | `trends_config.json` |
| Período | Últimos 24 meses desde la corrida | `fetch_trends.py:84` |
| Región | La que indique `geo` de esa señal en `trends_config.json` | `trends_config.json` |
| Señal | `momentum` (nivel promedio reciente) + `dir` (comparación de dos ventanas de 10 semanas) + búsquedas relacionadas | `fetch_trends.py::fetch_one` |
| Metodología | `computeDecision()` — sin documento de definición aprobado equivalente al de v2 | `src/engine.js:104-169` |
| Modelo | Ninguno — es una fórmula de puntos fija, no calibrada estadísticamente | `src/engine.js` |
| Cálculo | Confianza (+5 a +40) + momentum×0.3 (tope 30) + dirección (±20/+15/0) + breakout/relacionadas (+5 o +15) + **corroboración manual con Pinterest Predicts (+15, id 10 → "Poetcore")** + penalización por scope | `src/engine.js:104-152` |
| Pronóstico | Etiqueta de decisión: Comprar / Probar / Monitorear / Evitar | `src/engine.js:154-166` |
| Incertidumbre | No comunicada al usuario — el score se muestra como un número limpio | `Dashboard.jsx` (no se encontró lenguaje de incertidumbre en este flujo) |

**Conclusión del caso:** la cadena es reconstruible en el código, pero con dos diferencias importantes frente al Caso 1: (a) no hay documento de metodología aprobado equivalente a `01-definicion-tendencia.md`, y (b) el eslabón "corroboración con Pinterest" es un juicio editorial manual (`pinterestCorroboracion` en `contexto.json`) sin ninguna validación estadística de que esa correspondencia prediga algo — pesa lo mismo (+15) que la señal medida de "Breakout" en Trends, sin distinguir su origen distinto en la interfaz.

---

## Regla general encontrada

**Cuando el usuario pregunta "¿por qué esta tarjeta dice esto?"**, Radar 2.0 puede responder con una cadena completa y verificable. v1 puede responder con una lista de razones (`reasons`), pero esa lista mezcla, sin distinguirlas explícitamente para el usuario final, señales medidas (Trends) con juicios editoriales manuales (Pinterest, prensa) — ambas contribuyen puntos al mismo score sin que el peso relativo de cada tipo de evidencia quede claro en la interfaz.
