# Release checklist — Evaluador de Tendencias / Radar 2.0

Generado por la auditoría del 2026-09-27. Marcar cuando de verdad se verificó, no cuando "probablemente ya está".

## Metodología
- [x] **(2026-09-27, parcial)** H-01 mitigado sin tocar `computeDecision()`: se agregó `clasificarPatron()` en `src/engine.js`, un indicador nuevo y separado que lee `yoy`/`persistencia`/`estacional` (que ya existían en los datos, sin usarse) y se muestra junto a cada tarjeta en `Dashboard.jsx` como un chip aparte ("Patrón: tendencia sostenida / estacional / pico aislado / caída sostenida"). El puntaje y la etiqueta de compra de las 30 señales quedaron exactamente iguales — verificado con `git diff --stat` (solo inserciones) y comparando `computeDecision()` antes/después. Ejemplo real ya visible en el panel: "Cuadros (gingham, Príncipe de Gales)" sigue en 71 puntos / "Comprar", pero ahora muestra "Patrón estacional" junto al badge. **Pendiente:** decidir qué hacer de fondo con `computeDecision()` — este chip informa, no corrige el puntaje. Revisar después del 9 de noviembre, como se acordó.
- [ ] Precision/recall por clase publicado para el Trend Score, no solo exactitud agregada (sección 8).
- [ ] Backtesting y Trend Score repetidos con muestra mayor, como recomiendan `hallazgo-backtesting-fase3.md` y `hallazgo-trend-score-fase4.md`.
- [ ] Verificado (con un caso real) si el riesgo de H-06 (umbrales absolutos sobre series re-escaladas) cambia algún veredicto ya publicado.

## Exposición pública
- [ ] `v2.html` restringido (robots, o autenticación mínima) hasta que su propia documentación confirme que está lista para producción, **o** el aviso "en construcción" se refuerza para que sea imposible de ignorar (hoy ya existe pero es un texto pequeño).
- [ ] `robots.txt` agregado si se decide seguir publicando ambas versiones mientras se completa la validación.

## Seguridad
- [x] Sin secretos en el historial de git (verificado 2026-09-27).
- [x] Sin credenciales hardcodeadas en el código (verificado 2026-09-27).
- [x] GitHub Actions ancladas a SHA exacto (ya implementado).
- [x] `npm audit` sin vulnerabilidades (verificado 2026-09-27).
- [ ] Confirmar que el Client Secret de MercadoLibre expuesto en la sesión del 2026-09-27 fue rotado.

## Calidad / pruebas
- [ ] Framework de pruebas instalado para el frontend (Vitest recomendado, ya usan Vite) — hoy `engine.js`, `Dashboard.jsx`, `engineV2.js`, `DashboardV2.jsx` tienen 0 pruebas automatizadas, contra 134 en el pipeline de Python.
- [ ] `computeDecision()`, `evaluarEmpresa()`, `mejorMercado()` y `evidencia()` cubiertos por pruebas.

## UX / comunicación de incertidumbre
- [ ] Aviso de "esto describe el pasado, no el futuro" movido del footer a junto al badge de estado en cada tarjeta de v2 (H-09).
- [ ] Terminología "momentum" revisada para no confundirse con "aceleración" (H-07), o al menos documentada la diferencia en el panel.
- [ ] Relación entre la lista de "Evidencia" y los pesos reales del Trend Score aclarada en el panel (H-04) — hoy puede leerse como respaldo aunque 2 de 5 variables pesen negativo.

## Datos / continuidad
- [ ] Plan de respaldo alternativo a `pytrends` (que sigue archivado desde abril 2025) documentado, aunque no se implemente todavía.
- [ ] Procedimiento de backup/restore de `data/v2/` y `src/data/` escrito, aunque git ya cumpla ese rol de facto.
- [ ] Segunda foto en `historial/` capturada en la fecha planeada (9 de noviembre de 2026 o después) antes de citar resultados de aciertos en material comercial.

## Monitorización (no bloquea el lanzamiento actual, sí un "LANZAMIENTO VERIFICADO" futuro)
- [ ] Alguna forma de detectar si `pytrends` empieza a fallar sistemáticamente, más allá de que alguien lo note al correr el script a mano.
- [ ] Alguna forma de comparar el rendimiento del Trend Score en el tiempo contra lo medido en la fase 4 (detección de degradación).
