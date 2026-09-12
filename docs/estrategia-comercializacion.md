# Estrategia de comercialización — de herramienta interna a servicio para clientes

**Contexto:** Ricardo es consultor (administración de negocios internacionales / inteligencia de mercados) y quiere ofrecer el Evaluador de Tendencias a empresas del sector moda para toma de decisiones de compra basadas en datos. Esta nota resume el diagnóstico de qué falta y en qué orden atacarlo, hecha tras comparar el proyecto contra el competidor Lexi (lexiapp.co) y auditar el estado actual de la herramienta (ver `claude/auditoria-2026-09.md` y `claude/evaluacion-lexi-funcionalidades.md`).

## Diagnóstico: qué hay hoy vs. qué se necesita para vender

| | Hoy | Para vender a terceros |
|---|---|---|
| Cobertura de las 3 preguntas de Lexi | Solo "qué diseñar" (tendencias color/prenda/material) | Falta "cuánto producir" y "dónde vender" con algo más que el campo `geo` |
| Dato que sostiene la recomendación | Solo tendencia pública (Google Trends, prensa, Pinterest Predicts, WGSN) | Cruce con el historial de ventas propio del cliente — es el verdadero diferenciador, no replicable por un competidor que solo mira tendencia pública |
| Fuente de datos | `pytrends`, librería no oficial de scraping | Riesgo de negocio real si se cobra por un servicio que depende de ella sin respaldo ni fuente alterna |
| Contenido editorial (WGSN, Heuritech, Accio.com) | Uso propio, lectura razonable | Revisar licencia antes de redistribuir esa lectura dentro de un producto que se cobra a un tercero |
| Evidencia de que funciona | Ninguna corrida comparativa todavía (la de sept-nov 2026 está en curso) | Necesaria antes de la primera venta — es el caso de estudio, no solo control de calidad interno |
| Operación | Ricardo edita `trends_config.json` y el `.jsx` a mano por archivo, un cliente (él mismo) | Sirve para 2-3 clientes piloto operados por Ricardo; no escala a autoservicio sin inversión de ingeniería |

## Roadmap propuesto

### Fase 1 — Cerrar la evidencia (ahora → noviembre 2026)
- Terminar el ciclo de comparación septiembre→noviembre ya en marcha (recordatorio programado para 2026-11-05).
- Documentar el resultado como el primer caso: qué señal se predijo, qué pasó realmente. Esto es lo que convence a un comité de compras, no una demo.

### Fase 2 — Construir el diferenciador real: cruce con ventas del cliente (prioridad #1)
Objetivo: que la recomendación de compra deje de basarse solo en tendencia pública y empiece a decir "esta señal + tu propio historial de ventas por región/canal = esto es lo que deberías comprar y dónde venderlo". Esto es lo que ningún competidor que solo lea Google Trends o WGSN puede ofrecer, porque depende del dato privado de cada cliente.

Pasos concretos:
1. Definir con el primer cliente piloto qué dato de ventas puede compartir (mínimo viable: unidades vendidas por referencia, color y ciudad/canal en las últimas 8-12 semanas — el mismo dato que ya pide `criterios-compra-materiales.md` en "Métricas a registrar").
2. Construir el cruce señal-de-tendencia × sell-through real: por cada señal del radar, ¿la empresa ya tiene una referencia parecida vendiendo bien o mal en esa región?
3. Esto también resuelve, de forma más barata que construir un motor de embeddings completo, buena parte de la característica de Lexi de "curvas de talla y mix por región desde vecinos similares" — con reglas simples sobre el propio historial del cliente, no necesita machine learning desde el día uno.

### Fase 3 — Piloto con 2-3 empresas del clúster Conecta Moda
- Ofrecer el radar operado por Ricardo (no autoservicio) a cambio de pago reducido o de caso de estudio documentado.
- Cada cliente cura sus propias 20-30 señales (Ricardo las carga a mano en esta fase — no hace falta un formulario todavía).
- Entregable: reporte periódico (mensual o trimestral) con las recomendaciones, igual que se opera hoy para Conecta Moda internamente.

### Fase 4 — Solo si hay tracción: producto multi-cliente
- Recién aquí vale la pena invertir en arquitectura multi-tenant (cada empresa con su cuenta, refresco automático de datos, onboarding propio de señales sin depender de Ricardo).
- Evaluar en ese punto reemplazar o complementar `pytrends` con una fuente más estable (dataset público de Google Trends en BigQuery, o un proveedor de trend data pago si el modelo de negocio ya lo sostiene).
- Revisar formalmente las licencias de las fuentes editoriales (WGSN, Heuritech, Accio.com) antes de que su lectura aparezca dentro de un producto que se cobra a terceros.

## Riesgos a vigilar en todas las fases
- **`pytrends` no oficial**: puede dejar de funcionar sin aviso. Mitigación actual: correrlo con frecuencia moderada y no depender de él como única fuente en un contrato comercial.
- **Redistribución de contenido de fuentes pagas**: aceptable para criterio propio, a revisar antes de exponerlo a un cliente externo como parte de lo que se cobra.
- **Cuatro fuentes de verdad del mismo criterio de compra** (`criterios-compra-materiales.md`, panel, artifact): cada cliente nuevo multiplica este problema si no se unifica antes de escalar.

## Próximo paso sugerido
Definir con Ricardo qué empresa(s) del clúster Conecta Moda podrían ser el piloto de la Fase 2-3, y qué dato mínimo de ventas estarían dispuestas a compartir — eso determina qué tan rápido se puede construir el cruce señal × ventas.

---

> **Nota al trasladar a este repositorio (2026-09-12):** el panel dejó de ser un artifact estático y pasa a ser un sitio publicable en GitHub Pages. Para la Fase 3 eso importa: cada empresa piloto puede tener su propia rama o su propio `src/data/`, y el entregable pasa de ser un PDF a ser un enlace. Ojo con el riesgo que ya está anotado arriba: una página de GitHub Pages es **pública**, así que el día que entren datos de ventas de un cliente hay que cambiar de esquema (repositorio privado + despliegue con autenticación), no publicarlos ahí.
