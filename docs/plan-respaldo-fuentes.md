# Qué pasa si `pytrends` deja de funcionar

`pytrends` (la librería no oficial que usan tanto `fetch_trends.py` de la v1 como `pipeline/fuentes/trends.py` de Radar 2.0) está **archivada desde el 17 de abril de 2025** — nadie la mantiene, y Google puede romperla sin aviso en cualquier momento. Es la única fuente con historia larga (2004–hoy) que este proyecto tiene hoy. Este documento no implementa un respaldo — deja escrito qué hacer si hace falta, para que la decisión sea barata cuando llegue el momento (ver `docs/v2/00-decisiones.md`, que ya identificó este riesgo desde la fase 0).

## Cómo se sabe que se rompió

- `fetch_trends.py` (v1): si `pytrends` falla, el script lanza el error de `pytrends` tal cual y no llega a escribir `src/data/trends.json` — el panel se queda con los datos de la corrida anterior, no se rompe, pero tampoco se actualiza.
- `pipeline/historia.py` (v2): tiene manejo explícito de bloqueo (`Bloqueado`, HTTP 429) con reintentos y backoff creciente; si varias series seguidas fallan, la corrida se detiene sola con un mensaje claro (`r.motivo`) en vez de seguir golpeando la fuente.

Ninguno de los dos monitorea esto de forma activa entre corridas del pipeline real — pero desde el 2026-09-27, `.github/workflows/monitor-fuente.yml` corre un chequeo aparte y barato cada lunes (una consulta chica, no las 474 series reales) y abre un issue de GitHub solo si falla. Ver el hallazgo de monitorización en `docs/auditoria-2026-09-27-prelanzamiento/AUDIT-REPORT.md`, sección 32, y el checklist correspondiente.

## Las alternativas, en el orden en que conviene probarlas

1. **API oficial de Google Trends (alpha).** Ya solicitada (ver `docs/v2/solicitud-api-trends.md`), a la espera de aprobación de Google. Ventaja: soportada oficialmente, escala consistente entre consultas. Limitación conocida: solo 5 años de historia (1800 días) — no alcanza para el backtesting a 24 meses de la v2, que necesita `timeframe="all"`. Serviría para refrescar la **señal actual** (fase 2 de Radar 2.0), no para rehacer el backtesting histórico.
2. **Forks comunitarios de `pytrends`** (`trendspy`, `pytrends-modern`, mencionados en `docs/v2/00-decisiones.md`). No evaluados todavía — antes de depender de uno, probarlo en vivo igual que se hizo con `pytrends` originalmente (verificar que de verdad trae historia larga y no solo los últimos meses).
3. **Proveedores de pago** (SerpApi, DataForSEO, Glimpse). Sin evaluar, costo desconocido, depende de que se defina presupuesto (sigue pendiente per `docs/v2/00-decisiones.md`).

## Por qué cambiar de fuente no significa reescribir el pipeline

Tanto `fetch_trends.py` (v1) como `pipeline/fuentes/trends.py` (v2) están diseñados para esto: v2 en particular tiene la fuente detrás de una interfaz explícita (`BackendPytrends` con `nombre` e `interes_en_el_tiempo(...)`) — el resto del pipeline (`senales.py`, `modelos.py`, `backtesting.py`, `calidad.py`) no sabe ni le importa de dónde vino el dato. Cambiar de proveedor es escribir un adaptador nuevo que cumpla esa misma interfaz (mismo patrón que ya se usó para `pipeline/fuentes/wikipedia.py` y `pipeline/fuentes/mercadolibre.py`, aunque esas dos terminaron descartadas por otras razones — ver `docs/v2/revision-fuentes-fase6.md`), no rehacer el pipeline completo.

## Qué NO resuelve este documento

- No decide cuál alternativa usar — eso depende de presupuesto y de que la API oficial apruebe el acceso, ninguno de los dos bajo control de este repositorio.
- No implementa ningún fallback automático (failover). Si `pytrends` se rompe hoy, el panel simplemente deja de recibir datos nuevos hasta que alguien note el error y decida qué hacer con esta lista.
