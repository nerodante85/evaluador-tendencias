# Auditoría de la aplicación — septiembre 2026

Cubre los 4 archivos vivos del proyecto (`trends_config.json`, `fetch_trends.py`, `fetch_macro.py`, las dos copias de `panel-tendencias.jsx`) más el artifact publicado `Radar de Compra Conecta Moda` (claude.ai/code/artifact/6d8f5360…) y `criterios-compra-materiales.md`. Prioridad: crítico → importante → menor.

## 🔴 Crítico — bloquea el objetivo de noviembre

### 1. Hoy no existe una línea base real para comparar contra noviembre
No hay `trends_live.json` en el proyecto — solo `trends_config.json` (la lista curada, sin datos de Trends) y dos copias de `panel-tendencias.jsx` con números de `momentum`/`traj` ya escritos a mano. Eso quiere decir que **`fetch_trends.py` nunca se ha corrido de verdad todavía**: los números que hoy se ven en el panel (17, 6, 14, 78…) son ejemplos ilustrativos de cuando se construyó el panel, no una lectura real de Google Trends de septiembre.

Consecuencia directa para tu objetivo: si `fetch_trends.py` se corre por primera vez en noviembre, no vas a tener con qué compararlo — la pregunta "¿acertó el radar?" necesita un dato de *antes* y un dato de *después*, y hoy solo existiría el de después.

**Qué hacer ya:** correr `fetch_trends.py` esta semana (no esperar a noviembre) y guardar `trends_live.json` con un nombre fechado (`trends_live_2026-09.json`), aparte del que el script sobreescribe. En noviembre, correr de nuevo, guardar igual (`trends_live_2026-11.json`), y comparar los dos archivos directamente — eso sí es una medición real de "¿subió o bajó lo que dijo el radar?".

### 2. El script sobreescribe su propio historial
`fetch_trends.py` y `fetch_macro.py` escriben siempre a los mismos nombres de archivo (`trends_live.json`, `macro_live.json`). Cada corrida borra la anterior. Sin el paso manual del punto 1 (copiar con fecha), es estructuralmente imposible acumular historial — no es un bug del código, es que falta el hábito/paso de guardarlo aparte. Vale la pena agregarlo al `README.md` como paso obligatorio, no opcional.

### 3. La comparación septiembre→noviembre tiene una trampa técnica que hay que tener presente
El "momentum" de Google Trends es un índice relativo (0-100) *normalizado dentro de cada consulta*, no un número absoluto. Si en septiembre pides el interés de "verde oliva ropa" y en noviembre lo vuelves a pedir por separado, cada corrida se normaliza contra su propia ventana de 24 meses — no son directamente la misma escala matemática, aunque en la práctica para una sola serie continua de 24 meses el punto de comparación (últimas semanas vs. semanas anteriores dentro de la misma serie) sigue siendo válido. Lo que **no** es válido es comparar el momentum de una señal contra el de otra distinta como si fueran unidades absolutas — eso el panel ya lo maneja bien (usa dirección y confianza, no solo el número pelado). Para la evaluación de noviembre, compara la traj/dirección de la misma señal en el tiempo, no el número de momentum entre señales distintas.

## 🟠 Importante

### 4. Dos copias de `panel-tendencias.jsx` que ya divergieron
Existen `panel-tendencias.jsx` (raíz) y `claude/panel-tendencias.jsx`, creados con ~30 minutos de diferencia. No son iguales:

| | raíz | claude/ |
|---|---|---|
| Señales incluidas | 20 (hasta id 20) | 26 (hasta id 26, incluye LatAm) |
| Soporte de tema claro/oscuro | No | Sí |
| Filtro por región | No | Sí |
| Filtra "ruido" en búsquedas relacionadas (ej. videojuego coreano) | No | Sí |
| Campos de datos | `live`/`geo` (no coinciden con lo que escribe `fetch_trends.py`) | `sinDatosSuficientes`/`geoUsado` (sí coinciden) |

La copia de `claude/` es la más nueva y la que de verdad calza con la salida de `fetch_trends.py`. La de la raíz quedó obsoleta pero sigue en el proyecto sin ninguna marca de "no usar esta". Riesgo real: alguien (tú, o yo en una sesión futura) abre la copia equivocada y edita ahí, y el trabajo se pierde o se duplica.

**Recomendación:** borrar `panel-tendencias.jsx` (raíz) o marcarlo explícitamente como versión vieja, y quedarte con una sola fuente de verdad en `claude/`.

### 5. Ninguna copia del panel tiene las 30 señales de `trends_config.json`
`claude/panel-tendencias.jsx` (la más completa) llega hasta el id 26. Le faltan las 4 señales más nuevas de `trends_config.json` (ids 27-30: textiles de performance, trazabilidad, oferta china de Cantón, y Luminous Blue — color del año 2027). El panel que ves hoy no refleja todo lo que ya decidiste incluir en la configuración.

### 6. Dato equivocado en `claude/panel-tendencias.jsx` (verificado contra la fuente real)
El panel dice que la alpaca es el **"segundo producto de exportación textil de Perú (US$27,7 millones)"**. Verifiqué la fuente (El Tiempo Perú, sobre datos ADEX) y el dato real es: **tercer producto, US$27,78 millones** — detrás de dos líneas de camisetas de algodón. `trends_config.json` sí tiene el dato correcto ("tercer producto..."); solo la copia manual en el jsx quedó mal escrita. Es exactamente el tipo de error de transcripción que aparece cuando el mismo dato vive en 3 archivos distintos.

### 7. Cuatro fuentes de verdad para el mismo contenido
El criterio de compra (los 6 factores, las 5 preguntas, el calendario, las métricas) está escrito por separado en: `criterios-compra-materiales.md`, las dos copias de `panel-tendencias.jsx`, y el artifact estático "Radar de Compra Conecta Moda". Ya hay evidencia de que se desincronizan (punto 6). Cada vez que cambies un criterio vas a tener que acordarte de tocar hasta 4 lugares.

### 8. Cita mal atribuida (no es fabricación, es atribución de más)
`trends_config.json` id 1 cita "Diario del Sur / HSB Noticias, jul. 2026" para el verde oliva. Revisé el artículo de HSB Noticias sobre Colombiamoda 2026 y **no menciona colores** — habla de siluetas y técnica artesanal. El color sí está confirmado, pero por Diario del Sur exclusivamente (verifiqué el artículo real: "Colores de moda en Colombia para el segundo semestre de 2026" — sí lista verde oliva, borgoña, azul petróleo y tonos tierra/arena, casi palabra por palabra). Vale la pena quitar "/ HSB Noticias" de esa fuente.

## 🟡 Menor / riesgo operativo a vigilar

### 9. `pytrends` es una librería no oficial
El propio `fetch_trends.py` ya lo advierte en sus comentarios. Es un riesgo real para noviembre: Google puede cambiar su API interna sin aviso entre ahora y entonces, y el script simplemente dejaría de funcionar (no es hipotético, le ha pasado a esta librería varias veces históricamente). Recomendación: correrlo ahora (ver punto 1) sirve también como prueba de que todavía funciona; si falla, mejor descubrirlo en septiembre que en noviembre.

### 10. Etiqueta de fuente desactualizada en el panel
Ambas copias del panel muestran el texto fijo `"Frankfurter API · {fecha}"` junto al dato de TRM. Pero el propio `fetch_macro.py` explica en su docstring que **se cambió de Frankfurter a datos.gov.co** porque Frankfurter no tiene el peso colombiano (daba error 404). El texto del panel nunca se actualizó — sigue mencionando la fuente vieja e incorrecta. Además, el script no emite ningún campo de "fuente" para el bloque `usdcop` en el `.js` que genera, así que ese texto seguirá desactualizado hasta que alguien lo edite a mano.

### 11. Heurística fragil para detectar "Breakout" en búsquedas relacionadas
`fetch_trends.py` marca una búsqueda como "Breakout" solo si `value == "5000"` o `formattedValue == "Breakout"`. Es una suposición sobre el formato interno de pytrends que puede cambiar entre versiones de la librería sin avisar. Bajo impacto (afecta solo el realce visual, no el dato base), pero es otro punto de fragilidad ligado al mismo problema del punto 9.

## ✅ Lo que audité y encontré correcto (para que no repitas el trabajo)
- Estructura de `trends_config.json`: 30 ids únicos, 30 códigos únicos, sin queries duplicadas, todos los `swatch` son hex válidos, coherencia `scope`/`geo` (global → geo vacío, el resto → código de país) sin excepciones.
- Arancel del 40% a confección importada bajo US$10/kg — confirmado contra La República / Decreto 2598.
- Paleta SS27 de WGSN/Coloro (Luminous Blue como color del año 2027, más Energy Orange, Pop Pink, Meadowland Green, Clay) — confirmado contra la fuente oficial de WGSN.
- Caída de futuros de algodón NY/ICE de ~88 a ~71-72 ¢/lb (mayo-junio 2026) e inventarios 2026/27 un 5,5 millones de pacas por debajo del año anterior — confirmado contra CottonWorks.
- Los 8 microtrends de Pinterest Predicts 2026 (Poetcore/Pura poesía, Expedición utilitaria/Caqui aventurero, Broche de oro, Azul bajo cero, Delicadeza salvaje, Extra celestial, Neodéco, Encaje) y el "88% de aciertos" — confirmado contra la fuente, con nombres traducidos/parafraseados razonablemente.
- Caída del 8% en exportaciones textiles peruanas y del 12,3% en compras de EE. UU. (id 25 / bloque LatAm) — confirmado.
- Colores tendencia Colombia 2S-2026 (verde oliva, borgoña, azul petróleo, tonos tierra/arena/mantequilla) — confirmado contra Diario del Sur (dos artículos distintos, ver punto 8).

No alcancé a verificar de forma independiente las señales de Asia (Heuritech/Deeka AI, Accio.com) — son agregadores de pago o de acceso limitado; su lectura editorial es razonable pero no la pude confirmar contra fuente primaria. Si alguna de esas señales termina siendo la base de una compra grande, vale la pena revisarla aparte antes de comprometer tela.

## Prioridad sugerida antes de noviembre
1. Correr `fetch_trends.py` y `fetch_macro.py` ya, guardar los resultados con fecha (punto 1-2).
2. Eliminar o marcar como obsoleta la copia raíz de `panel-tendencias.jsx` (punto 4).
3. Corregir el dato de alpaca en `claude/panel-tendencias.jsx` y la etiqueta "Frankfurter API" (puntos 6 y 10).
4. Agregar las señales 27-30 al panel (punto 5).

## Estado al 2026-09-05 — qué se resolvió y qué sigue abierto

**Resuelto:**
- Puntos 1-3 (línea base): corrida real ejecutada, guardada como `claude/trends_snapshot_2026-09-05.js` + `claude/macro_snapshot_2026-09-05.js`, con método de comparación para noviembre en `claude/linea-base-septiembre-2026.md`.
- Punto 4: copia raíz de `panel-tendencias.jsx` eliminada. Única fuente de verdad: `claude/panel-tendencias.jsx`.
- Punto 5: señales 27-30 agregadas al panel.
- Punto 6: dato de alpaca corregido (tercer producto, US$27,8M) en el panel y en `trends_config.json`.
- Punto 10: `fetch_macro.py` ya emite el campo `fuente`; el panel lo lee dinámicamente con "TRM oficial · datos.gov.co" como respaldo.
- `claude/panel-tendencias.jsx` ya corre con los números reales de la corrida de septiembre (no los de ejemplo).
- `fetch_trends.py` y `trends_config.json` del proyecto actualizados a la v2 que Ricardo tenía localmente: agrega `yoy`, `persistencia`, `volatilidad`, `volumen`, `estacional` por señal (separa tendencia real de pico estacional y de ruido) y guarda automáticamente `historial/AAAA-MM-DD.json` en cada corrida — cubre el punto 2 (historial) de forma automática hacia adelante.

**Sigue abierto:**
- Punto 7 (cuatro fuentes de verdad para el mismo criterio de compra) — no se ha tocado.
- Punto 8 (cita "HSB Noticias" mal atribuida en id 1) — no se ha corregido.
- Punto 9 (riesgo de que pytrends deje de funcionar) — sin mitigación, solo mitigado por correr temprano.
- Punto 11 (heurística `value == "5000"` para Breakout) — sigue igual en la v2; es el formato estándar que usa pytrends para señalar Breakout, así que el riesgo es solo si esa librería cambia su convención interna, no un error de lógica.
- **`computeDecision()` (el motor de puntaje del panel) todavía no usa los campos nuevos de la v2** (`yoy`, `persistencia`, `volatilidad`, `estacional`). Hoy solo pondera confianza + momentum + dirección + breakout + Pinterest + scope, así que un pico estacional (`estacional: true`) puede seguir marcándose como "Comprar" aunque el propio dato diga que es un pico de calendario. Ricardo decidió posponer este cambio para "cuando sea necesario" — no es un bug, es una mejora pendiente de priorizar.

## Actualización 2026-09-12 — traslado a repositorio

El proyecto pasó de documentos de Claude a un repositorio de código (React + Vite, publicable en GitHub Pages). Eso cierra parcialmente dos puntos abiertos:

- **Punto 7 (cuatro fuentes de verdad):** el panel ya no lleva los datos escritos adentro. `src/data/trends.json` y `src/data/macro.json` los escriben los scripts, y `src/data/plan.json` / `src/data/contexto.json` son los únicos lugares donde vive el criterio editorial. Sigue habiendo duplicación entre `docs/criterios-compra-materiales.md` y `src/data/plan.json`, pero bajó de cuatro lugares a dos.
- **Punto 2 (historial que se sobreescribe):** sin cambio en el mecanismo, pero ahora cada corrida queda además en el historial de git.

Lo demás sigue igual que arriba.

## Auditoría full stack — 2026-09-12

Auditoría técnica completa (arquitectura, frontend, seguridad, accesibilidad, rendimiento, DevOps) con Claude Code, ya con el proyecto viviendo en el repositorio. Es un ejercicio distinto al de arriba: aquella auditoría revisaba contenido y datos; esta revisó código. Resultado: sin hallazgos críticos — no hay backend, base de datos ni autenticación que comprometer. Se encontraron y corrigieron 7 puntos, todos ya en `main` (commits `e9c62f6` y `94528e9`) y verificados en el sitio publicado.

**Corregidos:**

1. **Bug de colisión de IDs en el autodiagnóstico.** `agregarPropia` calculaba el `id`/`code` de una señal propia a partir de `propias.length`. Si borrabas una señal y agregabas otra, la nueva podía repetir el `id` de una que seguía en la lista — reproducible y verificado (agregar A y B, borrar A, agregar C: antes C se quedaba con el mismo `id` que B). Ahora usa un contador que solo crece (`propiaCounterRef`), en `src/Dashboard.jsx`.
2. **El autodiagnóstico no persistía nada.** `adoptadas`, `propias` y `nombre` vivían solo en memoria de React — un refresh borraba todo el trabajo marcado. Ahora se guardan en `localStorage` (clave `evaluador-tendencias:autodiagnostico:v1`), con `try/catch` por si el navegador lo bloquea.
3. **Labels del formulario de señal propia sin asociar a su input** (`FormularioSenal`) — fallaba WCAG 1.3.1/4.1.2. Ahora cada campo tiene `htmlFor`/`id`, y el selector de categoría usa `role="group"` + `aria-pressed`.
4. **Contraste de `--ink-soft` por debajo de AA.** El original (`#7E7E7D`) daba ~4.06:1 sobre el fondo, y se usa en casi todas las etiquetas y textos de apoyo del panel. Se cambió a `#6B6B6A` (~5.1:1) en `src/theme.js`.
5. **Sin favicon ni metaetiquetas Open Graph/Twitter.** Se agregó un favicon (swatch de color en el rust de acento, como SVG inline) y las metaetiquetas básicas en `index.html`, para que compartir el link muestre título y descripción.
6. **Acciones de GitHub Actions ancladas a tag mutable (`@v4`, `@v5`) en vez de a un commit.** Se anclaron las 5 acciones del workflow a su SHA exacto (verificado con `git ls-remote` contra el repo real de cada acción), con la versión como comentario. Hardening de cadena de suministro; el workflow no maneja secretos, así que el riesgo que cerraba era bajo.
7. **Heurística de "Breakout" en `computeDecision()` con un criterio redundante.** `hasBreakout` aceptaba tanto el literal `"Breakout"` como cualquier `crecimiento` con 4+ dígitos de porcentaje — pero `fetch_trends.py` nunca emite ese segundo formato salvo como texto libre de una búsqueda relacionada grande no etiquetada oficialmente como breakout. Se simplificó a solo el literal. **Esto sí movió el puntaje** de 4 señales con los datos del 12 de septiembre (13 Animal print, 18 Hanbok reinterpretado, 21 Artesanía elevada, 24 Resort y beachwear tropical: −10 puntos cada una) — se confirmó con Python contra los datos reales antes de aplicarlo y se le preguntó a Ricardo antes de tocar `engine.js`. Ninguna de las 4 cambió de categoría de decisión (Comprar/Probar/Monitorear/Evitar), y `historial/` no guarda el puntaje calculado, así que no afecta la comparación de la línea base de septiembre contra noviembre.

**Verificado, no solo revisado:**
- `npm run build`, `npm run dev`, `npm install` y `npm audit` corridos con Node real (v24.21.0) — build limpio, 0 vulnerabilidades, panel renderiza sin errores de consola.
- El bug de colisión de IDs y la persistencia se probaron a mano en el sitio publicado (agregar/borrar/agregar señales propias, recargar la página) — se comportan como se espera.
- Los dos deploys a GitHub Pages que llevaron estos cambios (runs #4 y #5 de `Publicar panel en GitHub Pages`) terminaron en éxito, y el sitio en vivo se revisó después de cada uno.

**No tocado, a propósito:** los campos `yoy`/`persistencia`/`volatilidad`/`estacional` de la v2 siguen sin usarse en `computeDecision()` (ver más arriba) — eso sigue siendo decisión pendiente de Ricardo, no algo que esta auditoría haya intentado resolver.
