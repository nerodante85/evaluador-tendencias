# Radar 2.0 — motor de señales, fase 2

Generado el 2026-09-27 por `python -m pipeline.cli senales`. Definición y umbrales: `docs/v2/01-definicion-tendencia.md` (aprobada por Ricardo el 2026-09-27). Código: `pipeline/senales.py`.

Series con historia suficiente para calcular señales (`apta_backtest`/`apta_senal` en la fase 1): **354** de 474 posibles.

## Puerta de salida: los casos de control

Si un caso de control no sale como se espera, es una señal de que el motor está mal calibrado — no se pasa a backtesting sin revisar esto primero. **La mayoría de los casos marcados ✗ abajo se investigaron y tienen una explicación real en los datos (picos históricos ya pasados, estacionalidad de fin de año), no un error de cálculo — ver `docs/v2/hallazgo-pico-vs-tendencia.md` antes de leer un puntaje bajo aquí como una falla.**

| Esperado | Nodo | CO | MX | ES |
|---|---|---|---|---|
| pico | `estilo.barbiecore` | (sin datos usables) | (sin datos usables) | (sin datos usables) |
| pico | `estampado.tie_dye` | baja_sostenida ✗ | estable ✗ | pico_atencion ✓ |
| pico | `estilo.cottagecore` | baja_sostenida ✗ | baja_sostenida ✗ | pico_atencion ✓ |
| pico | `estilo.mob_wife` | (sin datos usables) | (sin datos usables) | (sin datos usables) |
| alza | `prenda.pantalon_cargo` | pico_atencion ✗ | alza_sostenida ✓ | estable ✗ |
| alza | `corte.baggy` | pico_atencion ✗ | estable ✗ | estable ✗ |
| alza | `corte.pierna_ancha` | (sin datos usables) | alza_sostenida ✓ | alza_sostenida ✓ |
| baja | `corte.skinny` | alza_sostenida ✗ | estable ✗ | estable ✗ |
| estacional | `prenda.traje_bano` | estable | estable | pico_atencion |
| estacional | `prenda.abrigo` | estable | pico_atencion | pico_atencion |
| estacional | `tela.lana` | estable | estable | pico_atencion |
| estable | `prenda.camiseta` | estable ✓ | estable ✓ | estable ✓ |
| estable | `tela.algodon` | alza_sostenida ✗ | alza_sostenida ✗ | alza_sostenida ✗ |

**8 de 23** series de control con dato usable clasificaron como se esperaba (estacional no tiene una sola etiqueta que se le pueda exigir a `etiquetar()` — se lee aparte, en la tabla siguiente).

### Estacionalidad de los controles estacionales

| Nodo | CO | MX | ES |
|---|---|---|---|
| `prenda.traje_bano` | False | False | True |
| `prenda.abrigo` | False | True | True |
| `tela.lana` | True | True | True |

## Distribución por mercado

| Mercado | alza_sostenida | baja_sostenida | pico_atencion | estable | no_evaluable | sin_ventana |
|---|---:|---:|---:|---:|---:|---:|
| CO | 13 | 3 | 6 | 79 | 0 | 0 |
| MX | 15 | 4 | 15 | 89 | 0 | 0 |
| ES | 13 | 1 | 38 | 78 | 0 | 0 |

## Distribución por tipo de nodo

| Tipo | Mercado | alza_sostenida | baja_sostenida | pico_atencion | estable | no_evaluable | sin_ventana |
|---|---|---:|---:|---:|---:|---:|---:|
| color | CO | 4 | 0 | 0 | 20 | 0 | 0 |
| color | MX | 4 | 0 | 1 | 22 | 0 | 0 |
| color | ES | 3 | 0 | 2 | 22 | 0 | 0 |
| corte | CO | 1 | 0 | 1 | 10 | 0 | 0 |
| corte | MX | 3 | 0 | 2 | 17 | 0 | 0 |
| corte | ES | 1 | 0 | 7 | 14 | 0 | 0 |
| estampado | CO | 0 | 1 | 1 | 5 | 0 | 0 |
| estampado | MX | 1 | 0 | 0 | 6 | 0 | 0 |
| estampado | ES | 1 | 0 | 3 | 5 | 0 | 0 |
| estilo | CO | 2 | 1 | 1 | 3 | 0 | 0 |
| estilo | MX | 1 | 3 | 1 | 6 | 0 | 0 |
| estilo | ES | 1 | 1 | 6 | 6 | 0 | 0 |
| prenda | CO | 3 | 1 | 2 | 27 | 0 | 0 |
| prenda | MX | 3 | 1 | 8 | 22 | 0 | 0 |
| prenda | ES | 2 | 0 | 11 | 21 | 0 | 0 |
| tela | CO | 3 | 0 | 1 | 14 | 0 | 0 |
| tela | MX | 3 | 0 | 3 | 16 | 0 | 0 |
| tela | ES | 5 | 0 | 9 | 10 | 0 | 0 |