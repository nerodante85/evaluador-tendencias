# Hallazgo (auditoría 2026-09-27): la escala 0-100 de cada serie puede no representar lo que se habría visto en vivo en un corte histórico

Este hallazgo viene de H-06 en `docs/auditoria-2026-09-27-prelanzamiento/AUDIT-REPORT.md`. Se investigó con datos reales antes de escribirlo aquí — no es una sospecha teórica.

## El mecanismo

`pipeline/historia.py` descarga cada serie **una sola vez**, con `timeframe="all"` (`pipeline/fuentes/trends.py`). Google Trends normaliza el índice 0-100 contra el punto más alto **de toda la ventana consultada** — para una consulta descargada hoy (2026), eso incluye información de 2026, incluso cuando se usa esa misma serie para simular un corte de, digamos, 2015.

Una consulta que un empresario hubiera hecho en vivo en 2015 habría normalizado contra el pico visto **hasta 2015**, no contra el pico de toda la historia. Si el término creció mucho después, el pico "hasta 2015" es más chico que el pico global — así que los valores de 2015 en la serie descargada hoy están, en términos relativos a su propio momento, **más comprimidos hacia abajo** de lo que se habrían visto en vivo.

## Qué se probó

Con series reales ya descargadas (sin pedir nada nuevo a Trends), para cada serie clasificada `apta_backtest` y cada corte que el backtesting real usaría (después del calentamiento de `cortes_de_prueba`, muestra de 600 cortes de series elegidas al azar con semilla fija):

1. **Versión actual** — el tramo hasta el corte, tal como lo usa hoy el pipeline (en la escala 0-100 de la serie completa descargada).
2. **Versión simulada** — el mismo tramo, reescalado 0-100 contra **su propio máximo hasta ese punto** (lo más cercano que se puede reconstruir, sin volver a consultar Trends, a lo que una consulta en vivo habría mostrado en esa fecha).

Se corrió `etiquetar()` (la misma función de `pipeline/senales.py`, sin modificar) sobre ambas versiones y se comparó la etiqueta resultante a 24 meses.

**Resultado: de 600 cortes probados, 310 (51.7%) dieron una etiqueta distinta** entre la versión actual y la simulada — en varios casos el signo del crecimiento se invierte por completo (de `alza_sostenida` con +64% a `baja_sostenida` con -67%, por ejemplo, en `prenda.chaleco` CO).

## Qué significa esto, con precisión — no todo lo mismo

Esto **no** significa que la comparación entre modelos (naive vs. Holt-Winters vs. SARIMA, `docs/v2/reporte-backtesting-fase3.md`) esté necesariamente mal: esa comparación siempre usa la **misma** serie, con la **misma** escala, tanto para ajustar el modelo (`conocida = valores[:corte+1]`) como para la etiqueta real de referencia — así que modelo contra baseline se sigue comparando en igualdad de condiciones entre sí, caso por caso (McNemar pareado). Lo que está en duda es otra cosa, más de fondo:

**La propia definición de "qué pasó realmente" en un corte histórico (la etiqueta `etiqueta_real`, usada como verdad de referencia en todo el backtesting) puede no representar lo que un empresario habría visto de verdad en esa fecha.** El motivo técnico exacto: `crecimiento`, `persistencia`, `volatilidad` y `saturación` son razones (cocientes) y por sí solas son invariantes a un reescalado uniforme — pero `PISO_RUIDO = 5` en `senales.py` y los umbrales de volumen absolutos de `calidad.py` (`media36 ≥ 8`, etc.) **no lo son**: son constantes fijas en la escala 0-100, y esa escala cambia de significado según cuánto haya crecido la serie después del corte.

## Lo que no se puede afirmar todavía

- No se puede decir "el backtesting está mal" sin más — la comparación relativa entre modelos parece razonablemente robusta a esto (mismo razonamiento de arriba).
- No se validó si esto cambia el **veredicto final** de la fase 3 (si `holt_winters`/`sarima` le siguen ganando al baseline a 24 meses) — eso requeriría rehacer el backtesting completo con una fuente de datos verdaderamente histórica, que no existe sin volver a consultar Trends con `timeframe` truncado por cada corte (miles de consultas adicionales — el mismo riesgo de bloqueo de `pytrends` que ya limita este proyecto).
- La escala del efecto (51.7%) es real para el experimento descrito, pero **el experimento en sí es una aproximación**: reescalar el tramo histórico contra su propio máximo es lo más cercano que se puede simular sin datos nuevos, no una reproducción exacta de lo que Trends habría devuelto en vivo en esa fecha exacta.

## Qué hacer con esto

No se cambia ningún código de `pipeline/senales.py` ni `pipeline/calidad.py` en esta auditoría — cambiar un umbral que ya se usó para calibrar y validar el sistema existente exige el mismo proceso que ya sigue el proyecto para `01-definicion-tendencia.md`: decisión de Ricardo, con fecha y motivo, y repetir el backtesting completo después. Se deja como recomendación, no como corrección aplicada:

1. **Corto plazo (barato):** documentar esta limitación donde se citen los resultados del backtesting — no presentar la exactitud reportada (43–53% según horizonte) como si viniera de una simulación perfectamente fiel al pasado.
2. **Mediano plazo:** evaluar si `PISO_RUIDO` y los umbrales de `calidad.py` deberían ser relativos a la historia disponible hasta cada punto, no un valor absoluto fijo — pero esto cambiaría resultados ya publicados y necesita el mismo proceso de aprobación que cualquier cambio a la definición de tendencia.
3. **Largo plazo (caro):** si alguna vez se consigue la API oficial de Google Trends con acceso a descargas por rango de fechas fijo (`docs/v2/00-decisiones.md`), sería la única forma de eliminar esta limitación de raíz en vez de aproximarla.

## Reproducir esto

```python
from pipeline.senales import etiquetar
from pipeline.calidad import inicio_historia_util, metricas, clasificar
from pipeline.backtesting import cortes_de_prueba, MESES_MAX
import json

valores = [v for _, v in json.load(open("data/v2/raw/trends/CO/prenda.chaleco.json", encoding="utf-8"))["serie"]]
corte = 150  # un corte real que el backtesting usaría
tramo = valores[: corte + 1]
pico_local = max(tramo) or 1
tramo_simulado = [round(v / pico_local * 100) for v in tramo]

print("actual:  ", etiquetar(valores, corte, horizonte=24).etiqueta)
print("simulado:", etiquetar(tramo_simulado + valores[corte + 1 :], corte, horizonte=24).etiqueta)
```
