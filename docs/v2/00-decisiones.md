# Radar 2.0 — decisiones de la fase 0

Fecha: 2026-09-26. Este documento fija lo que se decidió antes de escribir código de la v2 y por qué. Lo que dice "verificado" se comprobó ese día; lo que dice "afirmación de terceros" viene de páginas de proveedores que venden alternativas, así que no se toma como cierto sin probarlo.

## Producto y público

Radar 2.0 se ofrece a **empresarios de la confección y diseñadoras**. No depende del taller de Ricardo ni del clúster Conecta Moda: la v1 nació ahí, pero la v2 se diseña como producto general.

Consecuencias:
- Los datos de la demostración no pueden ser de ningún taller ni cliente concreto.
- `plan.json` (telas, presupuesto, calendario) es criterio editorial de Ricardo para su taller. La v2 no lo hereda: responde "qué considerar diseñar o comprar", no "qué telas compra este taller".
- Cuando entren datos de ventas de un usuario, aplica la regla de `CLAUDE.md`: repositorio privado y despliegue con autenticación antes de subir un solo dato.

## Mercados

**Colombia (CO), México (MX) y España (ES).** Sin mercado global por ahora.

El español no es uno solo: jean / jeans / vaqueros, chaqueta / chamarra, suéter / jersey, traje de baño / bañador. La taxonomía guarda una consulta por mercado (`taxonomia/*.yaml`, campo `q`) en vez de una sola para todos.

## Presupuesto

Sin definir. Se difiere y no bloquea la fase 1, que no cuesta nada. Para que la decisión sea barata cuando llegue, la descarga de datos va detrás de una interfaz (`pipeline/fuentes/trends.py`): cambiar de proveedor es escribir un adaptador, no rehacer el pipeline.

## Fuentes de datos: estado real

| Fuente | Estado | Nota |
|---|---|---|
| Google Trends vía `pytrends` | **Funciona hoy** (verificado 2026-09-26: 273 puntos mensuales 2004–2026 en 3 s). **Repositorio archivado desde el 17-abr-2025**, sin mantenimiento. | Riesgo alto y continuo: Google puede romperlo sin aviso. Es la única fuente con historia de 20 años. |
| API oficial de Google Trends (alpha) | Anunciada el 24-jul-2025. Acceso solo por solicitud. Escala consistente entre consultas, **pero solo 5 años (1800 días)**. | 5 años no alcanzan para un backtest de 24 meses, así que no reemplaza a `timeframe="all"`. Sí serviría para la señal actual. **Acción para Ricardo: solicitar acceso** en developers.google.com/search/apis/trends (es gratis y la lista de espera es lenta). |
| Proveedores de pago (SerpApi, DataForSEO, Glimpse) | No evaluados. Costo desconocido. | Respaldo natural si `pytrends` deja de funcionar. Depende del presupuesto. |
| Forks comunitarios (`trendspy`, `pytrends-modern`) | No evaluados. | Afirmación de terceros de que están mantenidos. Probar antes de depender. |
| Redes sociales | Fuera del alcance. | Sin acceso legal ni API utilizable. Se reevalúa si aparece. |
| Pinterest Trends, MercadoLibre, catálogos, pasarelas, Wikipedia | Sin verificar. | Fase 6. Cada una necesita revisión de acceso y términos de uso antes de comprometerla. |

Consecuencia de diseño: **una sola fuente en la fase 1**. Por eso el Trend Score de la fase 4 solo podrá calcular los factores medibles con búsquedas y deberá mostrar cuántos de los ocho tiene disponibles.

## Convivencia con la v1

- La v1 no se toca hasta la comparación del 9 de noviembre: `computeDecision()`, `src/data/trends.json`, `trends_config.json`, `fetch_trends.py` y `fetch_macro.py` quedan como están.
- La v2 vive aparte: código en `pipeline/`, taxonomía en `taxonomia/`, datos en `data/v2/`, y (desde la fase 5) salidas para el panel en `src/data/v2/`.
- Las 30 señales de la v1 se mapean a nodos de la taxonomía (`v1:` en cada nodo y `taxonomia/migracion_v1.yaml`), y una prueba automática verifica que ninguna quede sin destino.

## Nombres

`trends.json` ya declara `version: 2` y se refiere a la versión del script de la v1. Para no confundir: el producto nuevo es **Radar 2.0** y sus esquemas de datos llevan `esquema`, no `version`.

## Puertas

| Antes de… | Debe cumplirse |
|---|---|
| Fase 3 (predicción) | Definición de "tendencia" aprobada (`01-definicion-tendencia.md`) y cerrada antes de ver resultados de modelos |
| Fase 5 (panel) | Backtesting hecho: el horizonte que se anuncia sale de él |
| Fase 7 (ventas de usuarios) | Repositorio privado y despliegue con autenticación |
