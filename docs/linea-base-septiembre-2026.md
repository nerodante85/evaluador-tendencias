# Línea base de septiembre 2026 — para comparar en noviembre

**Fecha de captura:** 2026-09-05
**Por qué existe este documento:** `trends_live.js`/`macro_live.js` se sobreescriben cada vez que Ricardo corre los scripts, así que no sirven como punto de comparación. Esta es la foto fija de esa primera corrida real, guardada aparte para poder medir en noviembre si el radar acertó.

Archivos de esta corrida, guardados verbatim en el proyecto:
- `claude/trends_snapshot_2026-09-05.js` — salida completa de `fetch_trends.py` (30 señales)
- `claude/macro_snapshot_2026-09-05.js` — salida de `fetch_macro.py` (USD/COP)

## Hallazgo 1: el script que corriste ya no es el que está en el proyecto

La salida trae campos que **no existen** en la versión de `fetch_trends.py`/`trends_config.json` guardada aquí: `yoy` (variación interanual), `persistencia`, `volatilidad`, `volumen`, `estacional`. También cambió el texto de algunas notas (ids 6, 25) y el cálculo de "búsquedas relacionadas" ya no usa el heurístico frágil `crecimiento == "5000"` que señalé en la auditoría — ahora trae porcentajes reales tipo `+250%`, `+1150%`.

Esto es una mejora real (justo el punto débil que marqué como 🟠 en `auditoria-2026-09.md`), pero significa que tienes un `fetch_trends.py` v2 en tu máquina que el proyecto no conoce. Si quieres que quede como fuente única de verdad, compárteme ese script y `trends_config.json` actualizados y los sincronizo aquí — si no, cada vez que me pegues una salida nueva voy a tener que inferir qué cambió en vez de saberlo.

## Hallazgo 2: el `fetch_macro.py` que corriste es el de antes de mi corrección

La salida de macro **no trae el campo `fuente`** que agregué la sesión pasada (el que reemplaza la etiqueta vieja de "Frankfurter API"). Eso indica que corriste tu copia local, no la versión guardada en `claude/fetch_macro.py`. No rompe nada — el panel tiene un valor de respaldo ("TRM oficial · datos.gov.co") que se muestra cuando falta `fuente` — pero para que la etiqueta salga dinámica del dato real, la próxima vez copia `fetch_macro.py` desde el proyecto antes de correrlo.

## Lectura rápida de esta corrida

- De las 30 señales, 26 ya tienen dato real de Trends (`sinDatosSuficientes: false`); las 4 nuevas (27–30, agregadas la sesión pasada) siguen sin dato salvo la 30 (Luminous Blue), que sí trajo señal (`momentum: 17, subiendo`).
- Casi todas las señales de Colombia (`scope: "co"`) tienen `confianza: "baja"` — volumen de búsqueda bajo es normal en un mercado más chico; no es un error del sistema, es una limitante conocida de medir con Google Trends a nivel país pequeño (documentada en el README/metodología).
- Las señales con `confianza: "alta"` y mayor `volumen` (Fucsia eléctrico, Blazers largos, Animal print, Cuadros, Hanbok, Harajuku/Y2K, Crochet, Resort/beachwear) son las que más vale la pena mirar primero en noviembre — son las que Trends puede medir con solidez.
- USD/COP bajó de 3.202,8 (agosto) a 3.126,1 (5 sep.), tendencia "bajando" — peso más fuerte, favorece comprar tela importada en el corto plazo.

## Cómo comparar en noviembre

Cuando corras los scripts otra vez en noviembre, compara señal por señal contra este archivo:
1. **Dirección**: ¿las que estaban "subiendo" siguen subiendo, o se aplanaron/bajaron?
2. **Confianza**: ¿alguna de las `baja` subió a `media`/`alta` porque acumuló más semanas de dato?
3. **Sin datos suficientes → con dato**: ¿alguna de las señales 27–30 (o cualquier otra con `sinDatosSuficientes: true`) ya tiene número?
4. **`yoy`**: si el script v2 sigue calculando variación interanual, esa es la métrica más directa de "¿la tendencia editorial (prensa) se confirmó en búsqueda real?"

Nota de método (ya documentada en el proyecto): el `momentum` de Google Trends está normalizado por consulta, no es una unidad absoluta comparable entre señales distintas — sí es válido comparar la misma señal en el tiempo (que es justo lo que hace este ejercicio de septiembre vs. noviembre).

---

> **Nota al trasladar a este repositorio (2026-09-12):** los dos snapshots citados arriba están ahora en `historial/trends_snapshot_2026-09-05.js` e `historial/macro_snapshot_2026-09-05.js`, sin cambios. Los mismos datos, ya en el formato que lee el panel, están en `src/data/trends.json` y `src/data/macro.json`.
