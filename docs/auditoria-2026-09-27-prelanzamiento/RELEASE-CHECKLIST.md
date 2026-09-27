# Release checklist — Evaluador de Tendencias / Radar 2.0

Generado por la auditoría del 2026-09-27. Marcar cuando de verdad se verificó, no cuando "probablemente ya está".

## Metodología
- [x] **(2026-09-27, parcial)** H-01 mitigado sin tocar `computeDecision()`: se agregó `clasificarPatron()` en `src/engine.js`, un indicador nuevo y separado que lee `yoy`/`persistencia`/`estacional` (que ya existían en los datos, sin usarse) y se muestra junto a cada tarjeta en `Dashboard.jsx` como un chip aparte ("Patrón: tendencia sostenida / estacional / pico aislado / caída sostenida"). El puntaje y la etiqueta de compra de las 30 señales quedaron exactamente iguales — verificado con `git diff --stat` (solo inserciones) y comparando `computeDecision()` antes/después. Ejemplo real ya visible en el panel: "Cuadros (gingham, Príncipe de Gales)" sigue en 71 puntos / "Comprar", pero ahora muestra "Patrón estacional" junto al badge. **Pendiente:** decidir qué hacer de fondo con `computeDecision()` — este chip informa, no corrige el puntaje. Revisar después del 9 de noviembre, como se acordó.
- [x] **(2026-09-27)** Precision/recall por clase agregado a `pipeline/backtesting.py` (`precision_recall_por_clase`, con pruebas) y publicado en `docs/v2/reporte-backtesting-fase3.md` y `data/v2/backtesting.json`. Reveló H-19 (ver abajo) — exactamente el tipo de cosa que este ítem del checklist buscaba encontrar.
- [x] **(2026-09-27)** Backtesting y Trend Score repetidos con muestra mayor (280 de 314 series `apta_backtest`, antes 150 — casi el doble): la conclusión de la fase 3 se sostiene (holt_winters/sarima le ganan al baseline solo a 24 meses). Trend Score: exactitud 0.639 vs. mayoría 0.625, AUC 0.655 (antes 0.660/0.649/0.675 con muestra chica — mejora modesta se sostiene con más evidencia). **Hallazgo nuevo en el camino: H-19, el baseline que "gana" a 6-12 meses tiene recall 0.0 para `alza_sostenida`** — ver `docs/v2/hallazgo-recall-fase3.md`.
- [x] **(2026-09-27)** H-06 verificado con datos reales — y el riesgo es más grande de lo estimado en la auditoría original: de 600 cortes históricos reales (los que el backtesting sí usaría), **51.7% cambian de etiqueta** al simular la escala que se habría visto en una consulta en vivo en esa fecha, contra la escala actual (que incorpora todo lo que pasó después). La comparación relativa entre modelos (naive vs. Holt-Winters vs. SARIMA) parece robusta a esto porque usa la misma escala en ambos lados — lo que está en duda es la propia definición de "qué pasó realmente" en un corte histórico, la verdad de referencia contra la que se mide todo. Detalle completo, metodología reproducible y qué NO se puede afirmar todavía: `docs/v2/hallazgo-escala-historica-fase3.md`. No se tocó `pipeline/senales.py` ni `pipeline/calidad.py` — cambiar esos umbrales exige el mismo proceso de aprobación que `01-definicion-tendencia.md`.

## Exposición pública
- [x] **(2026-09-27)** H-02 resuelto con la opción proporcionada por GitHub Pages (sin autenticación real, que exigiría repositorio privado — reservado para cuando entren datos de clientes, per `CLAUDE.md`): `public/robots.txt` con `Disallow: /v2.html` para todos los crawlers, más `<meta name="robots" content="noindex, nofollow">` directo en `v2.html` (más confiable que robots.txt solo, ya que no depende de que el crawler lo respete). El `<title>`, la meta `description` y el `og:description`/`og:title` ahora dicen explícitamente "en construcción" — así que hasta un link compartido sin abrir la página avisa que no es el producto terminado. Verificado en el build (`dist/robots.txt` y `dist/v2.html`).
- [ ] Quitar el `noindex` de `v2.html` cuando Radar 2.0 se dé por listo para lanzamiento general (repetir muestra de calibración más grande, backtesting con más series — ver checklist de "Metodología" arriba).

## Seguridad
- [x] Sin secretos en el historial de git (verificado 2026-09-27).
- [x] Sin credenciales hardcodeadas en el código (verificado 2026-09-27).
- [x] GitHub Actions ancladas a SHA exacto (ya implementado).
- [x] `npm audit` sin vulnerabilidades (verificado 2026-09-27).
- [x] Client Secret de MercadoLibre rotado — confirmado por Ricardo (2026-09-27).

## Calidad / pruebas
- [ ] Framework de pruebas instalado para el frontend (Vitest recomendado, ya usan Vite) — hoy `engine.js`, `Dashboard.jsx`, `engineV2.js`, `DashboardV2.jsx` tienen 0 pruebas automatizadas, contra 134 en el pipeline de Python.
- [ ] `computeDecision()`, `evaluarEmpresa()`, `mejorMercado()` y `evidencia()` cubiertos por pruebas.

## UX / comunicación de incertidumbre
- [ ] Aviso de "esto describe el pasado, no el futuro" movido del footer a junto al badge de estado en cada tarjeta de v2 (H-09).
- [ ] Terminología "momentum" revisada para no confundirse con "aceleración" (H-07), o al menos documentada la diferencia en el panel.
- [ ] Relación entre la lista de "Evidencia" y los pesos reales del Trend Score aclarada en el panel (H-04) — hoy puede leerse como respaldo aunque 2 de 5 variables pesen negativo.

## Datos / continuidad
- [x] **(2026-09-27)** Plan de respaldo alternativo a `pytrends` documentado en `docs/plan-respaldo-fuentes.md` — no implementado (depende de presupuesto y de aprobación externa), pero las alternativas y el orden en que probarlas quedan escritos.
- [x] **(2026-09-27)** Procedimiento de backup/restore escrito en `docs/procedimiento-backup-restore.md` — confirma qué vive en git (casi todo) y qué no (`data/v2/.secretos/`, a propósito), con los comandos exactos de restauración.
- [ ] Segunda foto en `historial/` capturada en la fecha planeada (9 de noviembre de 2026 o después) antes de citar resultados de aciertos en material comercial.

## Monitorización (no bloquea el lanzamiento actual, sí un "LANZAMIENTO VERIFICADO" futuro)
- [x] **(2026-09-27)** `.github/workflows/monitor-fuente.yml` — chequeo semanal (lunes, barato: una sola consulta chica, no las 474 series reales) de si `pytrends` sigue funcionando. Si falla, abre un issue de GitHub una sola vez (no uno por semana mientras siga caído); si vuelve a funcionar, lo cierra solo. Lógica en `pipeline/monitor_fuente.py`, con pruebas (backend falso, sin red). También se puede correr a mano: `python -m pipeline.cli monitor-fuente`.
- [x] **(2026-09-27)** `pipeline/historial_metricas.py` — cada vez que se recalibra el Trend Score (`python -m pipeline.cli trend_score`), se agrega una entrada a `data/v2/trend_score_historial.json` (append-only) y se avisa por consola si el AUC cayó ≥0.05 contra la calibración anterior, o si la exactitud dejó de superar la clase mayoritaria. No decide nada solo — la decisión de qué hacer con una caída real sigue siendo de Ricardo, igual que cualquier cambio de metodología. Con pruebas.
- **Lo que esto NO resuelve:** no hay forma de automatizar "¿el modelo acertó de verdad?" sin esperar meses de datos reales — eso sigue siendo el backtesting offline (`pipeline/backtesting.py`), a mano. Esto solo detecta si el número de la propia calibración se cae de golpe entre una corrida y la siguiente, no si la predicción se cumplió en el mundo real.
