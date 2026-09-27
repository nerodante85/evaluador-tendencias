# Radar 2.0 — plan

Objetivo: demostrar **por qué** una tendencia crece, **qué tan consistente** es y **qué tan confiable** es su proyección, para empresarios de la confección y diseñadoras en Colombia, México y España. Las decisiones de fondo están en `00-decisiones.md`; qué cuenta como "tendencia" está en `01-definicion-tendencia.md`.

```
Fuentes → Normalización → Motor de señales → Modelo predictivo → Backtesting → Trend Score → Panel
```

## Reglas

1. La v1 no se toca hasta la comparación del 9 de noviembre de 2026.
2. Pipeline en Python que escribe JSON versionado; el panel sigue siendo estático. Sin backend hasta que haya datos de usuarios.
3. Los pesos del Trend Score no se ponen a mano: se calibran con backtesting. Si un modelo no le gana al baseline, el panel lo dice.
4. El score solo usa factores medibles y muestra cuántos de los ocho tiene (con solo Trends no existen "diversidad de fuentes" ni "adopción").
5. Toda frase del panel sale de campos calculados y es probabilística; nunca "será".

## Fases

| Fase | Entregable | Puerta de salida | Estado |
|---|---|---|---|
| 0. Decisiones | `00-decisiones.md`, `01-definicion-tendencia.md` | Definición de tendencia aprobada por Ricardo | Escrita (2026-09-26); falta su aprobación |
| 1. Taxonomía y datos | `taxonomia/` (158 nodos), `pipeline/`, historia de Trends en CO/MX/ES en `data/v2/raw/`, `reporte-calidad-fase1.md` | Informe de calidad: cuántos nodos tienen datos utilizables | **Hecha.** 474/474 series descargadas, 0 fallidas. 314 `apta_backtest`, 40 `apta_senal`, 108 `insuficiente`, 12 `sin_datos`. Detalle y el ajuste de categoría de Trends en `00-decisiones.md` |
| 2. Motor de señales | `pipeline/senales.py`: crecimiento, aceleración, persistencia, volatilidad, saturación y estacionalidad. Clasificación del estado actual (alza/baja sostenida, pico de atención, estable, no evaluable) con la misma regla aprobada en la fase 0 | Validado contra los casos de control — no como "todos deben salir como se esperaba" (algunos "fallos" resultaron ser hallazgos reales, ver `hallazgo-pico-vs-tendencia.md`), sino como "cada desacuerdo se investigó y tiene explicación en los datos" | **Hecha.** 63 pruebas. `docs/v2/reporte-senales-fase2.md`, `data/v2/senales.json` |
| 3. Predicción y backtesting | `pipeline/modelos.py` (naive estacional, media móvil, Holt-Winters, SARIMA; Prophet queda pendiente, es pesado y opcional) + `pipeline/backtesting.py` (ventana móvil, horizontes 6/12/24, test de McNemar pareado + corrección de Bonferroni, referencia de clase mayoritaria) | Un modelo por familia solo si le gana al baseline con significancia real | **Hecha.** Primera corrida (36 series × 5 cortes): ningún modelo ganaba — sospecha de tamaño de muestra. Corrida grande (150 series × 10 cortes, 17.056 evaluaciones): confirmada. **`holt_winters` y `sarima` le ganan al baseline a 24 meses** (significativo, sobrevive Bonferroni); a 6 y 12 meses sigue sin haber ganador, se queda `naive_estacional`. Ver `docs/v2/hallazgo-backtesting-fase3.md`. 108 pruebas. `docs/v2/reporte-backtesting-fase3.md`, `data/v2/backtesting.json` |
| 4. Trend Score | `pipeline/trend_score.py`: regresión logística L2 sobre las 5 variables del motor de señales (crecimiento, aceleración, persistencia, volatilidad, saturación), calibrada contra `alza_sostenida` a 24 meses (el horizonte que la fase 3 validó). Pesos versionados con intervalos de confianza | Generaliza mejor que la referencia mínima en datos que el ajuste nunca vio | **Hecha.** 150 series × 10 cortes → 1333 filas. Fuera de muestra: exactitud 0.66 (mayoría 0.649), AUC 0.675. Dos pesos salieron con signo contrario al que asumía el brief (`volatilidad`, `saturación`, positivos en vez de negativos) — investigado, ver `docs/v2/hallazgo-trend-score-fase4.md`. 122 pruebas. `docs/v2/reporte-trend-score-fase4.md`, `data/v2/trend_score.json`, `data/v2/trend_score_pesos.json` |
| 5. Panel | `v2.html` + `src/DashboardV2.jsx` + `src/engineV2.js` (segundo punto de entrada de Vite, separado de la v1). `pipeline/exportar_panel.py` consolida taxonomía + calidad + señales + Trend Score + backtesting en `src/data/v2/catalogo.json`. Navegación por tipo y mercado, evidencia en lenguaje llano, sección de metodología con el historial de aciertos real | Revisión visual con Ricardo | **Hecha, pendiente de tu revisión visual.** `npm run build` limpio (comparte el chunk de `theme.js` con la v1), probado en el navegador sin errores de consola. 128 pruebas. La v1 no se tocó. |
| 6. Más fuentes | Adaptadores uno por uno; cada uno recalibra el score | Cada fuente supera su revisión de acceso y términos | Pendiente |
| 7. Datos de ventas | Ingesta de sell-through por usuario | Repositorio privado y despliegue autenticado | Pendiente |

## Riesgos

- **Backtesting circular** si la definición de tendencia se ajusta después de ver resultados. Por eso se fija en la fase 0.
- **Trends mide interés de búsqueda, no ventas.** El backtest valida lo primero.
- **A 24 meses puede que ningún modelo supere al baseline** en muchas categorías (pocos ciclos estacionales en la historia). El panel anunciará el horizonte fiable por categoría según el backtest.
- **Tamaño de muestra:** calibrar pesos con pocas series sobreajusta. Por eso la taxonomía es de ~150 nodos × 3 mercados y no de 30 señales.
- **`pytrends` está archivado** (abr. 2025). La descarga va detrás de una interfaz para poder cambiarla.

## Cómo correr lo que hay

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.cli validar     # valida la taxonomía
python -m pipeline.cli historia    # descarga (reanudable; --mercados CO,MX --tipos color --limite 6)
python -m pipeline.cli calidad     # genera docs/v2/reporte-calidad-fase1.md
python -m pytest pipeline          # pruebas
```
