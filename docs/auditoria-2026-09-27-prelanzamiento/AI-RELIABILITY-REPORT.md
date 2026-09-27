# Confiabilidad del motor estadístico — no hay IA generativa

Este archivo existe porque el skill de auditoría lo pide como "AI-RELIABILITY-REPORT.md", pensado originalmente para apps con LLM/RAG. Esta aplicación **no usa inteligencia artificial generativa en ningún punto** — se verificó explícitamente buscando llamadas a APIs de LLM (OpenAI, Anthropic, etc.) en todo `src/` y `pipeline/`: no hay ninguna. Todo el "pronóstico" sale de estadística clásica (regresión logística regularizada, suavizado exponencial, SARIMA) sobre datos numéricos, no de un modelo de lenguaje interpretando texto.

Por eso este informe cubre lo que sí aplica: **la confiabilidad del motor de señales y de los modelos de pronóstico**, no alucinación de texto.

## No hay riesgo de invención de datos, fuentes o cifras

Verificado: ningún componente genera texto libre a partir de un prompt. Las frases que aparecen en el panel (`evidencia()` en `src/engineV2.js`, los `reasons` de `computeDecision()` en `src/engine.js`) son plantillas de texto fijo con valores numéricos interpolados — nunca texto generado. No pueden "inventar" una fuente, una fecha o una cifra que no exista en los datos, porque no hay un paso generativo en el camino.

## El riesgo real: sobre-interpretación de una salida numérica real

No es alucinación, pero es un riesgo de comunicación real y verificado (ver H-04 en `AUDIT-REPORT.md`): la lista de "Evidencia" que acompaña a cada tarjeta de Radar 2.0 presenta observaciones sobre variables individuales (`crecimiento`, `persistencia`, `aceleración`, `volatilidad`, `saturación`) de forma neutral, sin conectarlas explícitamente con el peso real que cada una tiene en el Trend Score calibrado. Dado que **dos de esas cinco variables (`crecimiento`, `aceleración`) tienen coeficiente negativo** en el modelo real (aunque no significativo — ver `docs/v2/hallazgo-trend-score-fase4.md`), un usuario puede leer "Crecimiento sostenido de búsquedas" como parte de por qué el score es alto, cuando en el modelo que efectivamente calcula ese score, esa variable no empuja en esa dirección.

**Esto está, además, explícitamente advertido por el propio equipo del proyecto** en `docs/v2/hallazgo-trend-score-fase4.md:31`: *"No se debería citar un peso individual... como si fuera una descomposición causal limpia."* La UI actual no viola esto de forma literal (no cita los pesos), pero sí presenta una lista de variables individuales junto al score de una forma que invita a esa misma lectura causal que el propio informe pide evitar.

**Recomendación:** o bien (a) agregar una nota junto a la lista de "Evidencia" aclarando que describe el estado de cada variable, no necesariamente lo que más pesó en el número de arriba, o (b) filtrar la lista para no incluir `crecimiento`/`aceleración` cuando su intervalo de confianza cruza cero (que es, de hecho, el caso reportado hoy).

## Confiabilidad de los modelos de pronóstico (resumen; detalle en AUDIT-REPORT.md sección 6-7)

- El backtesting es real y auditado: se verificó en el código que ningún modelo ve datos posteriores al punto de corte simulado.
- Ningún modelo se "elige por sofisticado": `comparar_contra_baseline()` exige significancia estadística (McNemar) + margen mínimo + supervivencia a la corrección de Bonferroni.
- A 24 meses, `holt_winters` y `sarima` le ganan de verdad al baseline (53.2% y 52.1% de exactitud contra 43.7% del baseline y 42.0% de la clase mayoritaria) — una mejora real, aunque en términos absolutos el sistema sigue equivocándose en casi la mitad de los casos a ese horizonte, y el propio panel lo comunica así.
- A 6 y 12 meses, ningún modelo le gana al baseline con evidencia estadística suficiente — el sistema correctamente se queda con `naive_estacional` en esos horizontes en vez de forzar un modelo más "impresionante".
- El Trend Score generaliza mejor que adivinar la clase mayoritaria en datos que nunca vio (AUC 0.675, exactitud 66.0% vs. 64.9%), pero la mejora sobre la vara mínima es modesta (+1.1 puntos porcentuales de exactitud) — no debería presentarse como una herramienta de alta certeza.

## Riesgo de degradación silenciosa (model drift)

No existe ningún mecanismo para detectar si, con el tiempo, el Trend Score deja de predecir tan bien como lo hizo en esta calibración (fase 4). Si Google Trends cambia su metodología de cálculo, o si el comportamiento real de las tendencias de moda cambia, el score seguiría produciendo números con la misma apariencia de confiabilidad sin que nadie lo note, salvo que alguien vuelva a correr el backtesting completo a mano.
