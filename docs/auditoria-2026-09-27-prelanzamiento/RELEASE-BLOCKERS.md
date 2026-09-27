# Release blockers — 2026-09-27

Solo lo que impide clasificar la app como lista para venderse activamente como herramienta de pronóstico. Ver `AUDIT-REPORT.md` para el detalle completo y la evidencia de cada uno.

## Bloqueadores reales

1. **H-01 — v1 no distingue tendencia de popularidad/estacionalidad/ruido.** `src/engine.js::computeDecision()` no usa `yoy`, `persistencia`, `volatilidad` ni `estacional`, pese a que `fetch_trends.py` ya los calcula. Es el motor que está en producción hoy. Mientras esto no se resuelva (incorporando las variables, o relabeleando explícitamente lo que v1 mide), cualquier afirmación comercial de "esto pronostica tendencias" sobre v1 es difícil de sostener frente a esta auditoría.
   - **Decisión requerida de Ricardo primero:** `CLAUDE.md` exige explicitar el impacto en los puntajes antes de tocar `engine.js` — no es una corrección que se pueda aplicar sola.

2. ~~**H-02 — Radar 2.0 ya está público antes de que su propia documentación diga que está lista.**~~ **Resuelto (2026-09-27):** `v2.html` sigue accesible por URL directa (GitHub Pages no permite autenticación real sin repositorio privado, que `CLAUDE.md` reserva para cuando entren datos de clientes), pero ahora tiene `noindex`/`nofollow`, `robots.txt` con disallow, y título/descripción que avisan "en construcción" incluso en un link compartido sin abrir. Ya no aparecerá en buscadores ni se presenta como terminado si alguien lo comparte. Sigue pendiente quitar el `noindex` cuando la muestra de calibración se amplíe, como piden los propios informes internos.

3. **La comparación septiembre-vs-noviembre no existe todavía** (solo una foto en `historial/`). No es un bug — es el calendario esperado — pero bloquea cualquier afirmación de "el radar acertó X%" en material comercial hasta el 9 de noviembre de 2026 o después.

## Verificar antes de cerrar (no bloquea el código, sí el checklist de seguridad)

4. **H-12 — Confirmar que el Client Secret de MercadoLibre expuesto en esta sesión ya fue rotado** en el DevCenter.

## Lo que NO es un bloqueador

- No hay vulnerabilidades de seguridad activas, secretos en git, ni dependencias con CVEs.
- La metodología de backtesting de v2 (McNemar + Bonferroni + baseline de clase mayoritaria) es sólida y está verificada en el código, no solo prometida.
- No hay IA generativa ni riesgo de alucinación de texto.
