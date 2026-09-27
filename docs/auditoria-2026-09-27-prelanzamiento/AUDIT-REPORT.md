# Auditoría de pre-lanzamiento — Evaluador de Tendencias (v1 + Radar 2.0)

**Fecha:** 2026-09-27. **Alcance:** todo el repositorio (`src/`, `engine.js`, `pipeline/`, `taxonomia/`, `data/`, `docs/`, `.github/workflows/`). **Modo:** solo lectura — ningún archivo de la aplicación fue modificado. Toda afirmación de este informe cita archivo y evidencia verificable; donde no se pudo verificar en vivo se marca explícitamente.

> Nota sobre el skill usado: `auditorapp` está diseñado originalmente para auditar aplicaciones de licitación pública (SECOP I/II). Esta aplicación no tiene nada que ver con contratación pública — es un radar de tendencias de moda sin IA generativa. Se siguió la estructura general del skill (evidencia, severidad, trazabilidad, release gate) pero se **omiten** las secciones específicas de SECOP/pliegos/RUP (no aplican) y se adaptan las secciones de "IA/RAG" a lo que esta app realmente tiene: un motor estadístico de señales y pronóstico, sin LLM. Los seis archivos se guardaron en `docs/auditoria-2026-09-27-prelanzamiento/` en vez de la raíz del repo, seso para no romper la convención de este repositorio de mantener `docs/` como único lugar de documentación.

---

## 1. Resumen ejecutivo

La aplicación tiene **dos motores independientes y de calidad muy distinta**, ambos ya publicados en el mismo sitio de GitHub Pages:

- **v1** (`src/engine.js` + `src/Dashboard.jsx`): en producción desde antes de este ciclo, usada activamente por Ricardo. Su motor de decisión (`computeDecision`) **no distingue una tendencia real de un pico estacional o de ruido de bajo volumen** — exactamente el riesgo central que esta auditoría fue encargada a evaluar — a pesar de que el propio script de descarga (`fetch_trends.py` v2) ya calcula las cuatro variables necesarias para hacer esa distinción (`yoy`, `persistencia`, `volatilidad`, `estacional`) y **no las usa**. Esto es una decisión documentada y deliberada (`CLAUDE.md`), no un bug oculto — pero para los fines de esta auditoría (¿la metodología distingue popularidad de tendencia futura?) es el hallazgo más importante del informe.
- **Radar 2.0 / v2** (`pipeline/` en Python + `src/DashboardV2.jsx`): metodológicamente mucho más sólido — backtesting real con test de McNemar pareado y corrección de Bonferroni, separación entrenamiento/prueba por serie completa (no por fila), baseline de clase mayoritaria en vez de 25% al azar, y una honestidad inusual en el propio panel público ("a 24 meses ningún modelo se acerca a la certeza"). Pero **ya está publicado en internet, indexable y con metadatos para compartir en redes**, pese a que sus propios informes internos dicen literalmente "antes de subir esto a producción vale la pena repetir con una muestra mayor" (`docs/v2/hallazgo-trend-score-fase4.md:32`) y pese a que `CLAUDE.md` trata a la v2 como "en construcción".

No se encontró IA generativa en ningún punto del sistema (se verificó: no hay llamadas a APIs de LLM en `pipeline/` ni en `src/`), así que el riesgo de "alucinación" en el sentido de invención de texto no aplica — pero sí existe un riesgo de **sobreinterpretación**: el panel de v2 muestra una lista de "Evidencia" por variable que puede leerse como respaldo de un puntaje, cuando dos de esas cinco variables (`crecimiento`, `aceleración`) tienen peso **negativo** (no significativo) en el modelo real que calcula ese mismo puntaje.

No se encontraron vulnerabilidades de seguridad activas, secretos filtrados en el historial de git, ni dependencias con CVEs conocidos. El punto de seguridad más concreto de esta sesión (un Client Secret de MercadoLibre expuesto en una captura de pantalla) ya fue señalado y se recomendó rotarlo en el momento; queda registrado aquí para el checklist.

**Veredicto (sección 32):** **NO LISTA** — ver razones en la sección de Release Gate al final de este documento.

---

## 2. Arquitectura encontrada

Dos aplicaciones React (Vite 6, multi-entry) que comparten solo `src/theme.js`:

| | v1 | Radar 2.0 |
|---|---|---|
| Entrada | `index.html` → `src/main.jsx` → `Dashboard.jsx` | `v2.html` → `src/main-v2.jsx` → `DashboardV2.jsx` |
| Motor | `src/engine.js` (JS, en el bundle del navegador) | `src/engineV2.js` (JS, solo lee JSON ya calculado) |
| Datos | `src/data/trends.json`, `macro.json`, `plan.json`, `contexto.json` — escritos por `fetch_trends.py`/`fetch_macro.py` (Python) o editados a mano (los dos últimos) | `src/data/v2/catalogo.json` — escrito por `pipeline/exportar_panel.py`, que consolida todo el pipeline Python |
| Cálculo pesado | Ninguno — el JS del navegador calcula el score en cada render con datos ya livianos | Todo el cálculo (señales, backtesting, regresión logística) ocurre en Python, offline; el navegador solo lee números ya calculados |
| Publicación | GitHub Pages, sin autenticación, ambas rutas en el mismo build (`vite.config.js` con `rollupOptions.input` multi-entry) | Igual — mismo `dist/`, mismo despliegue |

No hay backend, base de datos, ni servidor propio. Todo el "pipeline" corre localmente o vía scripts, y el resultado se versiona en git como JSON estático. Es una arquitectura deliberadamente simple, coherente con el alcance actual (sin datos de usuarios, sin autenticación).

---

## 3-4. Fuentes de datos y calidad de datos

| Fuente | Usa | Provider | Historial | Última actualización real | Cobertura | Licencia/condiciones | Qué pasa si deja de funcionar |
|---|---|---|---|---|---|---|---|
| Google Trends vía `pytrends` | v1 y v2 (ambas) | No oficial — repo `pytrends` **archivado desde abril 2025** (`docs/v2/00-decisiones.md:28`) | v1: 24 meses (`fetch_trends.py:84`); v2: `timeframe="all"` (2004–hoy) | v1: última corrida manual de Ricardo (no auditable desde el código — depende de cuándo se ejecutó `2-actualizar-datos.bat`); v2: `data/v2/raw/` con 474 archivos, cada uno con su propio `descargado` (fecha) | CO/MX/ES (v2), geo variable por señal (v1) | Sin términos de uso oficiales — es scraping de la interfaz pública de Trends | **No hay fallback.** Si Google bloquea `pytrends` (ya pasó como riesgo documentado), tanto v1 como v2 se quedan sin poder refrescar datos. `pipeline/fuentes/trends.py` está detrás de una interfaz intercambiable, así que técnicamente se puede sustituir, pero hoy no hay ningún backend alternativo implementado y activo. |
| TRM (tasa de cambio) | v1 solamente | Oficial — `datos.gov.co`, dataset del Banco de la República | ~120 registros (~90 días corridos) | Se regenera cada vez que se corre `fetch_macro.py` | Colombia únicamente | Datos abiertos del gobierno, gratis, sin llave | Si la API cae, `fetch_macro.py` lanza una excepción clara (`ValueError`) y no sobrescribe el dato anterior — comportamiento correcto. |
| Pinterest Predicts | v1 solamente | Editorial, reporte anual, cargado a mano en `src/data/contexto.json` | Anual | Depende de que alguien lo actualice cada diciembre (nota en el propio JSON: "Revisar cada diciembre") | Global | Contenido editorial de terceros, no una API | Si no se actualiza, el dato queda desactualizado silenciosamente — no hay ninguna alerta de "este dato tiene más de 12 meses". |
| Prensa (Diario del Sur, HSB Noticias) | v1 solamente, campo `note`/`source` en `trends_config.json` | Artículos periodísticos puntuales de 2026 | Un solo punto en el tiempo por señal | No se actualiza — son notas fijas en la configuración | Colombia (Norte de Santander) | N/A — cita editorial | **Hallazgo H-11 abajo**: no entra al cálculo del score (verificado en `engine.js`), pero se muestra en el panel sin ninguna indicación de que es una afirmación de un solo artículo de prensa, no un dato medido. |
| MercadoLibre, Wikipedia Pageviews, Pinterest Trends API | Ninguna — evaluadas y descartadas en la fase 6 | — | — | — | — | — | Ya resuelto: `docs/v2/revision-fuentes-fase6.md` documenta por qué cada una se descartó con evidencia real (acceso bloqueado, forma del dato inservible, o cobertura geográfica incompleta). No es un hallazgo nuevo de esta auditoría, se reafirma que la decisión está bien evidenciada. |

**Valores atípicos, duplicados, inconsistencias:** el pipeline de v2 tiene salvaguardas activas y **verificadas en el código, no solo documentadas**:
- `_es_degenerada()` (`pipeline/modelos.py:21`) evita que Holt-Winters/SARIMA cuelguen con series casi constantes — nacido de un bug real encontrado en pruebas.
- `inicio_historia_util()` (`pipeline/calidad.py:40`) descarta el tramo inicial de "ruido de bajo volumen" antes de que una serie cruce un piso mínimo, para no calentar los modelos con años de ceros.
- Semana parcial de Trends (`isPartial`) se descarta explícitamente en ambos scripts de descarga (`fetch_trends.py:97-102`, `pipeline/fuentes/trends.py` vía `historia.py:65-67`) — evita que una medición incompleta simule una caída falsa.

**Dónde el pipeline SÍ puede alterar/interpretar mal un dato (hallazgo nuevo de esta auditoría):** ver **H-06** en la sección 6 (data leakage) — los umbrales absolutos de "piso de ruido" y de volumen mínimo se aplican sobre series cuya escala 0-100 depende de la ventana completa descargada, no de lo que se habría visto en vivo en cada fecha histórica.

---

## 5. Metodología de tendencias

Radar 2.0 distingue explícitamente, con una función y una definición documentada y aprobada por Ricardo (`docs/v2/01-definicion-tendencia.md`, implementada en `pipeline/senales.py`):

| Concepto del brief de auditoría | ¿Existe en el código? | Dónde |
|---|---|---|
| Popularidad actual | Sí — `momentum` / `_momentum_reciente` (nivel promedio reciente) | `fetch_trends.py:245`, `exportar_panel.py:35-37` |
| Crecimiento | Sí — `crecimiento = F/B - 1` | `senales.py:82` |
| Aceleración | Sí — diferencia entre el crecimiento reciente y el de hace un año | `senales.py:109-118` |
| Tendencia emergente / consolidada | Parcial — el sistema no tiene una etiqueta distinta para "emergente" vs. "consolidada"; ambas caerían en `alza_sostenida` si cumplen el umbral. No es necesariamente un defecto (es una simplificación consciente a 4 etiquetas), pero el brief de auditoría pide diferenciarlas explícitamente y hoy no se puede desde el dato exportado. | `senales.py:38` (`ETIQUETAS`) |
| Tendencia estacional | Sí, y con una prueba deliberadamente estricta (coincide el mes del pico **y** sobresale sobre la mediana **y** no hay crecimiento fuerte que lo explique mejor) | `senales.py:148-175` |
| Tendencia en declive | Sí — `baja_sostenida` | `senales.py:95-96` |
| Saturación | Sí — nivel actual / máximo histórico | `senales.py:134-141` |
| Pronóstico futuro | Sí, pero **solo a 24 meses tiene evidencia real de que algún modelo le gane al baseline** (ver sección 7) | `pipeline/modelos.py`, `pipeline/backtesting.py` |
| Recomendación empresarial | Sí en v1 (`Comprar`/`Probar`/`Monitorear`/`Evitar`); en v2 el panel deliberadamente **no** da una recomendación binaria, solo un score 0-100 con contexto — decisión de diseño correcta y más conservadora que v1 | `engine.js:154-166` vs. `DashboardV2.jsx` |

**Hallazgo central (H-01):** v1, que es la versión ya usada activamente por Ricardo para decidir compras reales de tela, **no usa ninguna de las cuatro variables que distinguirían tendencia real de estacionalidad/ruido**, aunque el propio script las calcula desde hace tiempo. Ver detalle en Hallazgos.

---

## 6. Modelos predictivos y backtesting

Cuatro modelos con firma común (`pipeline/modelos.py`): `naive_estacional` (baseline real, no un modelo descartable), `media_movil`, `holt_winters`, `sarima`. Ninguno se elige "porque es más sofisticado" — la elección la decide `comparar_contra_baseline()` con evidencia estadística.

**Resultado real de la corrida más reciente (150 series × 10 cortes, 17.056 evaluaciones — `data/v2/backtesting.json`, verificado directamente):**

| Horizonte | naive (baseline) | media_movil | holt_winters | sarima | clase mayoritaria (vara mínima real) | ¿Algún modelo le gana con McNemar + Bonferroni? |
|---|---:|---:|---:|---:|---:|---|
| 6 meses | 81.6% | 75.7% | 81.5% | 81.7% | 74.0% | No |
| 12 meses | 62.9% | 58.3% | 62.7% | 64.3% | 59.1% | No |
| 24 meses | 43.7% | 41.2% | **53.2%** | **52.1%** | 42.0% | **Sí — holt_winters y sarima** |

Esto **es exactamente forecasting real, no extrapolación disfrazada**: el veredicto sale de comparar, en cortes históricos, lo que el modelo pronosticó (viendo solo datos hasta ese corte) contra lo que la serie realmente hizo después — verificado leyendo `evaluar_serie()` (`pipeline/backtesting.py:70-101`), que trunca la serie (`conocida = valores[:corte+1]`) antes de invocar cualquier modelo.

**Lectura honesta que hay que subrayar:** a 24 meses, el mejor modelo acierta ~53% de las veces sobre una vara mínima de 42% — una mejora real y estadísticamente significativa, pero en términos absolutos **el sistema se equivoca en casi la mitad de los casos a ese horizonte**. El propio panel lo dice ("ningún modelo se acerca a la certeza"), lo cual es correcto y debe mantenerse así.

**Bonferroni se aplica de verdad, no solo se menciona:** verificado en `pipeline/reporte_backtesting.py:97-99` — `alpha=0.05/n_pruebas` se recalcula explícitamente, no es una afirmación sin código detrás.

---

## 7. Data leakage

Se revisó específicamente:

- **Separación temporal en el backtesting:** correcta — `evaluar_serie()` nunca deja que un modelo vea datos posteriores al corte (`pipeline/backtesting.py:78`).
- **Separación train/test del Trend Score:** correcta y más rigurosa que el promedio — se separa por **serie completa**, no por fila (`pipeline/trend_score.py:90-100`), evitando que cortes de la misma serie contaminen entrenamiento y prueba.
- **H-06 (nuevo, no trivial): las series de Google Trends se descargan UNA sola vez con `timeframe="all"`** (`pipeline/fuentes/trends.py:14`, usado por `historia.py`) y se reutilizan para simular cientos de cortes históricos. Google Trends normaliza cada serie 0-100 contra el máximo **de toda la ventana consultada** — es decir, la escala de un punto de 2015 depende en parte de lo que pasó después de 2015 (incluida la porción "futura" respecto a cualquier corte histórico simulado antes de esa fecha).
  - **Lo que SÍ está a salvo:** todas las métricas que entran a `etiquetar()` y al Trend Score (`crecimiento`, `persistencia`, `volatilidad`, `saturación`) son **razones** (cociente entre dos puntos de la misma serie) — matemáticamente invariantes a un reescalado global positivo. Se verificó explícitamente: `crecimiento = F/B - 1`, `volatilidad = pstdev/media`, `saturación = media_reciente/máximo` — ninguna cambia si toda la serie se multiplica por una constante.
  - **Lo que NO está a salvo:** `PISO_RUIDO = 5` (`senales.py:33`) y los umbrales de volumen absoluto de `calidad.py` (`media36 ≥ 8`, `media24 ≥ 5`) son **valores absolutos**, no razones. Si el término creció mucho en años recientes, el "pico" que define el 100 de la escala es más alto que el que existía en, digamos, 2015 — lo que empuja los valores de 2015 hacia abajo en términos absolutos y puede hacer que un corte histórico caiga (o no) del lado equivocado de estos pisos, de una forma que no habría pasado con una consulta en vivo hecha en 2015.
  - **Impacto real:** esto no corrompe los aciertos ya reportados de forma directa (las etiquetas de tendencia son invariantes a escala), pero sí puede sesgar **qué cortes entran o no a la muestra de backtesting** vía `calidad.py` y `inicio_historia_util()`, ambos basados en umbrales absolutos. No se encontró evidencia de que esto ya haya pasado — es un riesgo estructural identificado, no un error confirmado con un caso concreto.
  - **Severidad:** MEDIA-ALTA. No invalida los resultados ya publicados, pero debe documentarse como limitación conocida y, si es barato, probarse con una serie real (comparar el punto de corte de `calidad.py` con y sin el tramo "futuro" del download) antes de citar el backtesting como validación completa.

- **Survivorship bias:** no aplica de forma clásica (no hay "empresas que sobrevivieron"), pero hay un sesgo de selección relacionado: solo los nodos con categoría `apta_backtest`/`apta_senal` entran a cualquier análisis — es decir, el sistema mide mejor los términos que YA tenían volumen suficiente, lo cual es correcto y transparente (se reporta la clase de calidad), no un leakage.

---

## 8. Falsos positivos y falsos negativos

No hay una tabla de matriz de confusión publicada (precision/recall por etiqueta), solo exactitud agregada. Dado que `alza_sostenida` es una de cuatro clases con clases desbalanceadas (la mayoritaria es "estable" en varios horizontes), la exactitud global puede esconder que el sistema falle sistemáticamente más en una dirección que en otra (p. ej., puede ser mejor detectando `estable` que detectando genuinos `alza_sostenida`, que es la etiqueta que más importa para una decisión de compra). **Recomendación:** publicar precision/recall por clase, no solo exactitud global, antes de usar el score para decisiones de negocio de alto valor.

**Consecuencia de un falso positivo** (dice que algo será tendencia y no lo es): compra de tela/inventario que no rota — costo financiero directo.
**Consecuencia de un falso negativo** (no detecta una tendencia real): oportunidad perdida frente a competidores — costo de oportunidad, más difícil de medir pero igual de real.

---

## 9-16. Taxonomía de moda (colores, materiales, prendas, cortes, estilos)

258 líneas de YAML, 6 archivos por tipo (`taxonomia/{prendas,cortes,telas,colores,estampados,estilos}.yaml`), cargados y **validados automáticamente** por `pipeline/taxonomia.py::validar()` — se verificó que la validación cubre: formato de id, consulta por mercado no vacía, consultas duplicadas, padre del mismo tipo, relaciones existentes, hex válido + familia reconocida para colores, y que ninguna de las 30 señales de v1 quede sin mapear a v2 (o explícitamente fuera de alcance). Esto es **trazabilidad real, no solo un README que lo promete** — `test_taxonomia.py` lo exige en cada corrida.

- **Colores:** hex + familia consistentes; medidos dentro de la categoría "Ropa" de Trends para no confundir el color con el sustantivo suelto — buena práctica, verificada en el comentario de cabecera de `colores.yaml`.
- **Override de categoría (`categoria: 0`)** para 6 nodos específicos (`cottagecore`, `tie_dye`, `punto`, `fibras_naturales`, `cachemira`, `mob_wife`): decisión basada en evidencia real (`00-decisiones.md`, tabla con antes/después), no arbitraria. Punto a favor de la metodología.
- **Consistencia de categorías durante el análisis:** sí — los ids son estables y versionados en git; un cambio de taxonomía es una diferencia de código auditable, no un valor mutable en tiempo de ejecución.
- **Regiones:** ver H-14 abajo — discrepancia real entre cómo v1 y v2 modelan "región".

---

## 17. Segmentación geográfica

- **v2** ata cada señal a un mercado real (`CO`/`MX`/`ES`) con su propio `geo` de Google Trends por consulta — el usuario puede saber exactamente de qué mercado sale cada dato (`m.query`, mostrado en el catálogo).
- **v1** usa `scope` (`co`/`latam`/`global`/`asia`) — una clasificación **editorial de distancia cultural**, no un mercado medido. Una señal "global" en v1 no significa que Trends midió el mundo entero con la misma consulta en cada país — es una etiqueta puesta a mano en `trends_config.json`. **H-14**: esto es una inconsistencia real entre las dos versiones del producto: v2 corrigió exactamente este punto, v1 (la que está en producción hoy) sigue con el modelo más débil.
- Ningún dato de v2 mezcla mercados sin decirlo: verificado en `exportar_panel.py` — cada nodo lista sus mercados por separado (`por_mercado`), nunca los agrega en un promedio ciego.

---

## 18. Métricas del modelo

Reportadas con contexto completo (no como cifras sueltas): exactitud, AUC, y siempre junto a **n, horizonte, muestra, baseline** — se verificó que ningún informe de v2 dice "el modelo tiene X% de precisión" sin decir de qué corrida, cuántas series, qué horizonte. Esto es justo lo que pide la sección 15 del brief de auditoría, y ya se cumple.

Números exactos verificados (`data/v2/trend_score_pesos.json`): n_entrenamiento=951, n_prueba=382 (series nunca vistas), exactitud fuera de muestra=0.660 vs. mayoría=0.649 (+1.1 pp — mejora real pero modesta), AUC=0.675.

---

## 19. Incertidumbre

- V2 sí muestra intervalos de confianza al 95% para cada peso del Trend Score (`trend_score_pesos.json:intervalos_95`) — y el propio informe advierte cuando un intervalo cruza cero ("esa variable no aporta con la evidencia actual").
- El panel público (`DashboardV2.jsx:122`) muestra el AUC junto al score, en lenguaje llano ("acierta el X% de las veces mejor que el azar").
- **No hay intervalo de confianza ni rango mostrado junto al score individual de cada tarjeta** (solo el número 0-100) — el usuario ve un puntaje puntual, no un rango. Es una limitación de presentación, no de cálculo (los datos para construir un rango ya existen).
- V1 no muestra ningún tipo de incertidumbre — el score se presenta como un número limpio con una etiqueta de decisión, sin ningún lenguaje de probabilidad.

---

## 20. Trazabilidad

Ver `DATA-TRACEABILITY-REPORT.md` para la cadena completa reconstruida caso por caso. Resumen: **v2 tiene trazabilidad real** (cada número en el catálogo se puede rastrear hasta el archivo JSON crudo de Trends, la consulta exacta, y el código que lo transformó). **v1 tiene trazabilidad parcial**: el score final lista sus "razones" (`reasons` en `computeDecision`), lo cual es bueno, pero el cálculo mismo no ha sido validado contra ningún historial real (no hay backtesting de v1).

---

## 21. Alucinaciones y generación de información

No hay IA generativa en el sistema (verificado: `grep` de imports/llamadas a APIs de LLM en todo `src/` y `pipeline/` no encontró ninguna). El riesgo de "invención" clásico de un LLM no aplica. El riesgo real y verificado es otro, más sutil: **H-04**, la lista de "Evidencia" del panel de v2 puede leerse como una explicación causal del score aunque dos de sus cinco variables tengan peso negativo (no significativo) en el modelo real — no es una invención de datos, es una posible sobre-interpretación de datos reales, presentados sin conectar explícitamente con los pesos reales del modelo.

---

## 22. Seguridad

- Sin backend propio → superficie de ataque mínima (sitio estático).
- `git log --all` sobre nombres de archivo de secretos/tokens/`.env`: **sin resultados** — no hay evidencia de secretos commiteados en ningún momento del historial.
- `grep` de patrones típicos de credenciales hardcodeadas en todo el código fuente: **sin resultados**.
- GitHub Actions ancladas a SHA exacto, no a tag mutable (`.github/workflows/deploy.yml`) — buena práctica de cadena de suministro, ya implementada.
- `npm audit --omit=dev`: **0 vulnerabilidades**.
- **H-12**: durante esta misma sesión de trabajo, un Client Secret de MercadoLibre quedó expuesto en texto plano en una captura de pantalla compartida en el chat. Se recomendó rotarlo en el momento. **Acción pendiente de confirmar:** verificar que Ricardo efectivamente lo rotó en el DevCenter de MercadoLibre antes de cerrar este hallazgo.
- `data/v2/.secretos/` (donde cae el token de MercadoLibre localmente) está correctamente en `.gitignore` — verificado, nunca se subió.
- No se probó explotación activa (fuera de alcance para una app estática sin backend ni formularios que acepten input no confiable).

---

## 23. Privacidad y derechos de uso de datos

- No se recopilan datos personales de usuarios del sitio (no hay analytics, cookies, ni formularios de captura verificados en el código).
- Los datos de Google Trends son agregados y anónimos por diseño de la propia API.
- **Pinterest Predicts**: contenido editorial de un tercero, citado como fuente — no se redistribuye el reporte completo, solo se referencia; riesgo de propiedad intelectual bajo.
- **Prensa** (`trends_config.json`): se cita la fuente (`source`) junto a cada nota — atribución presente, correcto.
- `pytrends` scrapea la interfaz pública de Google Trends sin API oficial — zona gris de términos de uso, ya documentada como riesgo por el propio proyecto (`00-decisiones.md`), no oculta.
- No se identificó ningún dato que requiera revisión jurídica más allá de lo ya anotado por el propio proyecto sobre el uso de `pytrends`.

---

## 24. APIs

No hay APIs propias expuestas (sitio estático). Las únicas integraciones salientes son: Google Trends (no oficial), `datos.gov.co` (oficial), y el adaptador de MercadoLibre recién construido (`pipeline/fuentes/mercadolibre.py`) que **no está conectado a ningún flujo activo** — quedó descartado con evidencia (ver conversación previa a esta auditoría, ya documentado en `docs/v2/revision-fuentes-fase6.md`).

---

## 25. Manejo de errores

- `fetch_macro.py`: si la API no devuelve registros, lanza `ValueError` explícito y **no sobrescribe** el archivo anterior — correcto.
- `pipeline/historia.py`: reintentos con backoff creciente ante bloqueo (429), y se detiene limpio tras varios fallos seguidos en vez de seguir golpeando la fuente — correcto y ya probado en producción (esta misma sesión usó ese mecanismo).
- `pipeline/modelos.py`: cualquier modelo que falle cae a `media_movil` en vez de tumbar todo el backtesting — correcto, con guarda adicional (`_es_degenerada`) para series casi constantes que antes colgaban el proceso.
- **v1 no tiene un estado explícito de "información insuficiente para pronosticar"** — cuando `confianza === "baja"`, el label queda forzado a `"Monitorear"`, lo cual es razonable, pero el usuario ve una etiqueta de decisión igual que las demás, no un mensaje distinto de "no hay suficiente evidencia". v2 sí lo hace mejor: `score_24m: null` se muestra literalmente como "sin score" en la tarjeta (`DashboardV2.jsx:101`) — cumple la regla del brief de preferir decir "no alcanza la evidencia" antes que inventar un número.

---

## 26. UX

Ver hallazgos H-07, H-08, H-09 (terminología "momentum", umbral de "bajando" no calibrado, badge de estado que describe el pasado). En positivo: v2 usa lenguaje explícitamente probabilístico y no promete certeza en ningún punto verificado del código de UI (`DashboardV2.jsx:122,278,332`) — esto cumple directamente la Regla 5 del propio `docs/v2/plan.md` ("toda frase del panel... nunca 'será'").

---

## 27. Rendimiento

- v1: todo el cálculo ocurre en el navegador sobre 30 señales — trivial, sin riesgo de rendimiento.
- v2: el navegador solo lee un JSON ya calculado (`catalogo.json`) — igualmente trivial. El trabajo pesado (backtesting, regresión) ocurre offline en Python, nunca en el cliente. Arquitectura correcta para este volumen de datos.
- No se identificaron cuellos de botella actuales. Advertencia a futuro: si `taxonomia/` crece mucho más allá de ~150 nodos × 3 mercados, `catalogo.json` crecería proporcionalmente y podría empezar a pesar en el bundle inicial — no es un problema hoy (no se midió el tamaño exacto del archivo en esta auditoría, recomendado como chequeo rápido antes de escalar la taxonomía).

---

## 28. Escalabilidad

- Más mercados/categorías: el diseño ya está pensado para esto (taxonomía versionada, pipeline con muestreo estratificado) — escalaría razonablemente bien en términos de código.
- Más usuarios del sitio: sitio estático en GitHub Pages, sin backend — escala sin esfuerzo hasta los límites de Pages (generosos para este tráfico esperado).
- Más frecuencia de actualización: **el cuello de botella real es `pytrends`** — no oficial, con pausas obligatorias entre consultas (8-10 segundos) y riesgo de bloqueo — 474 series ya tardan más de una hora. Esto no escala linealmente sin mover a una fuente de pago o a la API oficial de Trends (aún pendiente de aprobación, per `docs/v2/00-decisiones.md`).

---

## 29. Dependencias

**JS (producción):** `react`, `react-dom`, `lucide-react` — 3 paquetes, versiones recientes (18.3.x), 0 vulnerabilidades reportadas por `npm audit`. Riesgo de vendor lock-in: mínimo.

**Python:** `pytrends` (**archivado desde abril 2025** — riesgo real y ya documentado extensamente por el propio proyecto), `pandas`, `requests`, `pyyaml`, `pytest`, `statsmodels`. Ninguna dependencia pesada o inusual; `statsmodels` es una librería madura y ampliamente usada para exactamente este propósito (Holt-Winters, SARIMA, regresión logística regularizada).

**Servicio único sin alternativa activa:** Google Trends (vía `pytrends`) es la única fuente de datos con historia larga hoy. Si se bloquea, no hay una fuente B ya conectada — riesgo real, ya conocido y monitoreado por el proyecto, sin mitigación activa todavía.

---

## 30. Deploy

`.github/workflows/deploy.yml`: build con `npm ci` + `npm run build`, publicado a GitHub Pages vía Actions oficiales ancladas a SHA. Sin variables de entorno ni secretos en el workflow (no los necesita, es un sitio estático). Sin separación dev/producción explícita más allá de local (`npm run dev`) vs. publicado — razonable para el tamaño actual del proyecto. Sin mecanismo de rollback documentado más allá de revertir el commit y dejar que el workflow vuelva a correr (funciona, pero no está escrito en ningún lado como procedimiento).

---

## 31. Backups y recuperación

No hay un sistema de backup dedicado — pero **git ya cumple ese rol de facto** para todo lo versionado (`historial/`, `data/v2/raw/`, `src/data/`, taxonomía, código). No se encontró evidencia de que esto se haya declarado ni probado formalmente como estrategia de recuperación (ej. "si se corrompe `catalogo.json`, el procedimiento es X"). Dado que todo es regenerable desde `data/v2/raw/` + el pipeline, el riesgo real de pérdida de datos es bajo, pero el procedimiento no está escrito.

---

## 32. Monitorización

**No existe ningún mecanismo de monitorización activa**: no hay alertas si `pytrends` empieza a fallar sistemáticamente, no hay detección de *data drift* (¿cambió la distribución de las señales entrantes?) ni de *model drift* (¿el Trend Score sigue prediciendo tan bien como en la fase 4, o se degradó con el tiempo?). Todo el sistema es "bajo demanda": alguien corre un script y lee el resultado. Esto es razonable para el volumen actual de un solo operador, pero es una brecha real de cara a "LANZAMIENTO VERIFICADO" (que exige explícitamente detección de drift).

---

## 33. Riesgos empresariales

1. **Recomendaciones de v1 interpretadas como certeza** cuando la metodología detrás no distingue tendencia de estacionalidad/ruido (H-01) — el riesgo de negocio más directo: una compra de tela mal fundamentada.
2. **v2 públicamente visible antes de que su propia documentación diga que está lista** (H-02) — riesgo reputacional si un cliente potencial lo encuentra antes de la comparación de noviembre.
3. **Dependencia de una sola fuente de datos** (`pytrends`, no oficial, archivada) sin fallback activo — riesgo de continuidad del servicio completo, no solo de un dato.
4. **Comparación septiembre-vs-noviembre aún no realizada** — es la evidencia central de todo el caso comercial (`docs/estrategia-comercializacion.md`, `docs/linea-base-septiembre-2026.md`) y con una sola foto en `historial/` todavía no se puede hacer. Esto es un estado esperado del calendario (hoy es 2026-09-27, la comparación es el 9 de noviembre), no un fallo — pero cualquier material de venta que se muestre antes de esa fecha no debería citar resultados de aciertos que todavía no existen.
5. **Pesos editoriales no validados con peso real en el score** (H-03, H-11): la corroboración con Pinterest Predicts y el bono de "Breakout" en v1 pueden mover una decisión de "Monitorear" a "Comprar" sin haber sido nunca sometidos a backtesting.

---

## 34. Hallazgos por severidad

| ID | Severidad | Resumen |
|---|---|---|
| H-01 | **CRÍTICA** (para el objetivo de esta auditoría) | v1, en producción, no usa `yoy`/`persistencia`/`volatilidad`/`estacional` — no distingue tendencia real de estacionalidad o ruido, pese a que esas variables ya se calculan. |
| H-02 | **ALTA** | Radar 2.0 (`v2.html`) ya está público e indexable pese a que su propia documentación interna dice que necesita más muestra antes de producción. Verificado en vivo. |
| H-03 | ALTA | Bono de "Breakout" en v1 (+15 pts) basado en un umbral de Google Trends conocido por ser sensible a bases de volumen casi nulas — nunca backtesteado. |
| H-04 | ALTA | La lista de "Evidencia" en v2 puede leerse como respaldo del score aunque 2 de 5 variables tengan peso negativo no significativo en el modelo real. |
| H-05 | ALTA | Cero pruebas automatizadas en todo el frontend (v1 y v2) — el motor de decisión que sí genera una recomendación de compra accionable (`engine.js`) no tiene ni un test. |
| H-06 | **ALTA** (subida desde MEDIA-ALTA, 2026-09-27, con evidencia real) | Umbrales absolutos (`PISO_RUIDO`, pisos de volumen en `calidad.py`) aplicados sobre series re-escaladas con información "futura" respecto a cada corte histórico de backtesting. Verificado con 600 cortes reales: **51.7% cambian de etiqueta** bajo la escala que se habría visto en vivo. La comparación relativa entre modelos parece robusta; la "verdad de referencia" del backtesting, no tanto. Ver `docs/v2/hallazgo-escala-historica-fase3.md`. |
| H-07 | MEDIA | "Momentum" (v1 y v2) es en realidad un nivel promedio, no una tasa de cambio — inconsistente con "aceleración", que sí está bien calculada. |
| H-08 | MEDIA | Umbral de "bajando" en v1 (delta > 3 en serie semanal sin suavizar) no calibrado ni backtesteado, puede disparar "Evitar / dejar salir". |
| H-09 | MEDIA | El "estado actual" mostrado en cada tarjeta de v2 describe una ventana que terminó ~12 meses atrás; el aviso de que es retrospectivo está solo en el footer. |
| H-10 | MEDIA (informativa) | Solo existe una foto en `historial/` — la comparación sept-vs-nov aún no es posible. Estado esperado, no defecto. |
| H-11 | MEDIA | `pinterestCorroboracion` es un mapeo editorial manual sin validación estadística, y suma +15 puntos fijos en v1. |
| H-12 | MEDIA (de esta sesión, con acción pendiente) | Client Secret de MercadoLibre expuesto en una captura compartida — se recomendó rotar, pendiente de confirmación. |
| H-13 | ~~BAJA~~ **Resuelto (2026-09-27)** | Sin monitorización de caída de fuente ni drift de modelo. Resuelto con `.github/workflows/monitor-fuente.yml` (chequeo semanal de `pytrends`, abre/cierra un issue solo) y `pipeline/historial_metricas.py` (avisa si el Trend Score se degrada entre calibraciones). No resuelve la detección de *data drift* en el sentido estricto (cambios en la distribución de las señales entrantes) ni la validación automática contra resultados reales — eso sigue siendo el backtesting offline. |
| H-14 | BAJA | v1 usa "scope" editorial (co/latam/global/asia); v2 ya corrigió esto con mercados reales medidos — inconsistencia entre versiones. |
| H-15 | BAJA | Sin `robots.txt` en todo el sitio. |
| H-16 | BAJA | Scripts `.bat` de onboarding referencian un archivo (`deploy-workflow.yml`) que ya no forma parte del flujo real. |
| H-17 | INFO (positivo) | Dependencias JS mínimas, 0 vulnerabilidades de `npm audit`, GitHub Actions ancladas a SHA exacto. |
| H-18 | INFO (positivo) | El backtesting de v2 usa McNemar pareado + Bonferroni + baseline de clase mayoritaria — rigor verificado en el código, no solo prometido en la documentación. |
| H-19 | **ALTA** (nuevo, 2026-09-27) | El baseline que "gana" a 6 y 12 meses (`naive_estacional`) tiene recall 0.0 para `alza_sostenida` en 32.188 evaluaciones — nunca detecta una tendencia real a esos horizontes. No afecta al panel público hoy (el Trend Score solo usa 24 meses), pero expone un hueco real en el criterio de "puerta de salida" del backtesting, que solo mira exactitud agregada. Ver `docs/v2/hallazgo-recall-fase3.md`. |

---

## Plan de corrección priorizado

1. **Antes de cualquier material comercial que use v1:** decidir explícitamente entre (a) incorporar `yoy`/`persistencia`/`volatilidad`/`estacional` a `computeDecision()` con el análisis de impacto que `CLAUDE.md` ya exige, o (b) relabelear las afirmaciones de v1 para que digan "popularidad reciente + momentum de corto plazo", no "tendencia".
2. **Restringir la visibilidad de `v2.html`** (mínimo: `robots.txt` con disallow, o autenticación básica) hasta que se cumpla lo que su propia documentación pide antes de producción (muestra mayor en el Trend Score).
3. **Confirmar la rotación del Client Secret de MercadoLibre** expuesto en esta sesión.
4. **Agregar un aviso junto al badge de "estado actual"** en cada tarjeta de v2 (no solo en el footer) aclarando que describe una ventana que ya terminó, no una predicción.
5. **Publicar precision/recall por clase**, no solo exactitud agregada, antes de usar el Trend Score para decisiones de negocio de alto valor.
6. **Instalar un framework de pruebas para el frontend** (Vitest, dado que ya usan Vite) y cubrir al menos `computeDecision()`, `evaluarEmpresa()` y `mejorMercado()`/`evidencia()`.
7. Repetir el backtesting y el Trend Score con una muestra mayor, como los propios informes de fase 3 y 4 recomiendan.
8. Documentar (aunque sea brevemente) un procedimiento de backup/restore, aunque hoy git ya cumpla ese rol de facto.

## Actualización (2026-09-27, misma tarde)

Se implementó la opción "score nuevo en paralelo" para H-01, elegida explícitamente por Ricardo entre las alternativas planteadas: `src/engine.js` gana `clasificarPatron()`, un indicador informativo que lee `yoy`/`persistencia`/`estacional` (ya existían en `trends.json`, no se usaban en ningún lado) y `src/Dashboard.jsx` lo muestra como un chip separado en cada tarjeta ("Tendencia sostenida" / "Patrón estacional" / "Pico aislado" / "Caída sostenida"), con su propia leyenda explicativa (`PatronLegend`).

**`computeDecision()` no se tocó** — verificado con `git diff --stat` (solo inserciones en `engine.js`, cero líneas del cálculo original modificadas) y ejecutando el motor antes/después: los 30 puntajes y etiquetas de la foto de septiembre quedan idénticos. La comparación del 9 de noviembre sigue siendo válida.

Con datos reales de la foto de septiembre, el chip ya identifica casos concretos que antes eran invisibles: **4 de las señales actualmente en "Comprar" (Blazers largos y capas suaves, Animal print, Cuadros, Resort y beachwear tropical) están además marcadas `estacional: true`** — es decir, el propio dato ya decía "esto puede ser de calendario" desde la corrida de septiembre, y el panel nunca lo mostraba. También aparece un caso inverso interesante: "Hanfu y renacimiento textil tradicional chino" tiene un puntaje de compra modesto (42, "Probar en lote pequeño") pero el chip lo marca como "Tendencia sostenida" — la señal más parecida a una tendencia real de las 30 no es la que tiene el puntaje más alto.

**H-01 pasa de "sin mitigar" a "mitigado parcialmente"** en `RELEASE-CHECKLIST.md`. Sigue pendiente la decisión de fondo — qué hacer con `computeDecision()` en sí — que se revisará después del 9 de noviembre, como se acordó explícitamente para no invalidar la comparación.

## Actualización 2 (2026-09-27) — H-02 y H-12 resueltos

**H-12:** Ricardo confirmó que rotó el Client Secret de MercadoLibre expuesto en la captura de pantalla. Cerrado.

**H-02:** `v2.html` gana `<meta name="robots" content="noindex, nofollow">`, `public/robots.txt` (`Disallow: /v2.html`), y el `<title>`/`description`/`og:*` ahora dicen "en construcción" explícitamente — verificado en el build (`dist/robots.txt`, `dist/v2.html`). GitHub Pages no ofrece autenticación real sin pasar a repositorio privado, que `CLAUDE.md` reserva a propósito para cuando entren datos de un cliente — así que la mitigación proporcionada es dejar de indexarlo y avisar honestamente en cualquier vista previa compartida, no esconderlo del todo. La página sigue siendo alcanzable por quien tenga el link directo, lo cual es aceptable dado que no expone datos personales ni de clientes, solo metodología y agregados de Google Trends.

Con esto, los dos bloqueadores accionables de `RELEASE-BLOCKERS.md` quedan resueltos. Sigue pendiente el punto de fondo (H-01: decisión sobre `computeDecision()` de v1, después del 9 de noviembre) y la comparación septiembre-vs-noviembre en sí, que dependen del calendario, no de código.

## Actualización 3 (2026-09-27) — H-06 verificado con datos reales: el riesgo es mayor de lo estimado

Se probó directamente, con 600 cortes históricos reales (los que el backtesting sí usaría en la práctica, tomados de series ya clasificadas `apta_backtest`): reescalar cada tramo histórico contra su propio máximo hasta ese punto (lo más cercano que se puede simular a una consulta en vivo, sin pedir nada nuevo a Google Trends) y comparar la etiqueta resultante contra la que da la escala actual, que incorpora todo lo que pasó después del corte.

**Resultado: 51.7% de los cortes cambian de etiqueta.** No es un caso raro ni un efecto marginal — es la mayoría de los casos probados. Detalle completo, metodología reproducible paso a paso, y una lectura cuidadosa de qué SÍ y qué NO se puede afirmar con esto: `docs/v2/hallazgo-escala-historica-fase3.md`.

**Lectura precisa, no alarmista:** esto no significa necesariamente que el veredicto de la fase 3 (holt_winters/sarima le ganan al baseline a 24 meses) esté mal — esa comparación es entre modelos que siempre usan la misma serie con la misma escala en ambos lados, caso por caso (McNemar pareado), así que la comparación relativa parece razonablemente robusta. Lo que sí queda en duda es algo más de fondo: **la propia "verdad de referencia" contra la que se mide todo el backtesting** — si `alza_sostenida` en un corte de 2015 refleja lo que un empresario habría visto en 2015, o algo distinto, distorsionado por cuánto creció el término después. El motivo técnico: `crecimiento`, `persistencia`, `volatilidad` y `saturación` son razones, invariantes a un reescalado uniforme — pero `PISO_RUIDO` (senales.py) y los umbrales de volumen de `calidad.py` son constantes absolutas, y no lo son.

**H-06 sube de severidad: de MEDIA-ALTA a ALTA.** No se corrigió el código (cambiar esos umbrales exige el mismo proceso de aprobación que `01-definicion-tendencia.md` — decisión de Ricardo, con fecha y motivo, y repetir el backtesting completo). La recomendación inmediata y de costo bajo: **cualquier cita de la exactitud del backtesting (43–53% según horizonte) debe venir acompañada de esta salvedad**, no presentarse como una simulación perfectamente fiel al pasado.

## Actualización 4 (2026-09-27) — muestra grande + hallazgo nuevo (H-19): el baseline "ganador" a 6-12 meses nunca detecta una alza real

Se repitió el backtesting con 280 de las 314 series `apta_backtest` disponibles (antes 150) y 10 cortes cada una — 32.188 evaluaciones. Los números cambian poco frente a la muestra anterior (24 meses: naive 46.1% vs. holt_winters 55.1% / sarima 54.3%, ambos siguen ganándole al baseline con McNemar+Bonferroni; a 6/12 meses sigue sin haber ganador) — la conclusión de la fase 3 se sostiene con una muestra casi el doble de grande.

**Lo nuevo:** al agregar precision/recall por clase (parte de esta misma ronda de correcciones), aparece un hallazgo que la exactitud agregada no dejaba ver: **`naive_estacional` y `media_movil` — los "ganadores" a 6 y 12 meses — tienen recall de 0.0 para `alza_sostenida`: en 32.188 evaluaciones, nunca detectaron ni una sola tendencia real de las que sí ocurrieron.** Es una propiedad estructural de esos dos modelos (ninguno tiene componente de tendencia, así que no pueden proyectar crecimiento más allá de lo ya visto), no un accidente de esta muestra. Detalle completo: `docs/v2/hallazgo-recall-fase3.md`.

**Por qué esto no afecta al panel público hoy:** el Trend Score ya se calibró solo a 24 meses, antes de este hallazgo, precisamente porque ese era el único horizonte con señal real — esa decisión resultó ser más acertada de lo que se sabía en ese momento. Lo que sí queda expuesto es un hueco en la metodología de la "puerta de salida" (`comparar_contra_baseline`, que solo mira exactitud, nunca recall por clase) — si algún día se extiende el pronóstico a 6-12 meses con el mismo criterio, se podría adoptar en silencio un modelo ciego a la clase que justifica una compra. **Nuevo hallazgo H-19, severidad ALTA** — no bloquea el lanzamiento actual (el panel no expone esto), pero debe corregirse en la metodología antes de que alguien extienda el pronóstico a horizontes cortos.

Con la muestra grande, el Trend Score también se recalibró (`data/v2/trend_score_pesos.json`): exactitud fuera de muestra 0.639 vs. mayoría 0.625 (antes 0.660 vs. 0.649 con muestra chica — la mejora sobre la vara mínima sigue siendo modesta, ahora con casi el doble de evidencia detrás), AUC 0.655 (antes 0.675). Primera entrada registrada en el historial de calibraciones nuevo (`data/v2/trend_score_historial.json`, `pipeline/historial_metricas.py`) — sin alerta de degradación, es la primera vez que se registra.

## Criterios para una nueva auditoría

Repetir esta auditoría cuando: (a) se resuelva el punto 1 sobre v1, (b) `v2.html` deje de estar expuesto sin restricción o su documentación interna confirme que ya está listo para producción, (c) exista al menos una segunda foto en `historial/` para poder auditar aciertos reales, no solo metodología.
