# Radar 2.0 — calidad de los datos, fase 1

Generado el 2026-09-27 por `python -m pipeline.cli calidad`. Es un informe de datos, sin interpretación: la lectura está en `docs/v2/00-decisiones.md`.

Nodos en la taxonomía: **158** · mercados: CO, MX, ES · series posibles: 474.

Clases: `apta_backtest` (sirve para validar proyecciones a 24 meses), `apta_senal` (sirve para leer la señal actual pero no para backtestear), `insuficiente` (hay datos, pero poco volumen o poca historia), `sin_datos` (Trends no devolvió nada o falta descargar). Umbrales en `pipeline/calidad.py`.

## Por mercado

| Mercado | apta_backtest | apta_senal | insuficiente | sin_datos |
|---|---:|---:|---:|---:|
| CO | 86 | 15 | 51 | 6 |
| MX | 108 | 15 | 32 | 3 |
| ES | 120 | 10 | 25 | 3 |

## Por tipo de nodo

Cada celda: `apta_backtest / apta_senal / insuficiente / sin_datos`.

| Tipo | CO | MX | ES |
|---|---|---|---|
| color | 23 / 1 / 6 / 0 | 24 / 3 / 3 / 0 | 25 / 2 / 3 / 0 |
| corte | 8 / 4 / 12 / 0 | 19 / 3 / 2 / 0 | 20 / 2 / 2 / 0 |
| estampado | 6 / 1 / 5 / 3 | 6 / 1 / 7 / 1 | 9 / 0 / 5 / 1 |
| estilo | 3 / 4 / 17 / 1 | 9 / 2 / 13 / 1 | 11 / 3 / 9 / 2 |
| prenda | 30 / 3 / 2 / 0 | 31 / 3 / 1 / 0 | 32 / 2 / 1 / 0 |
| tela | 16 / 2 / 9 / 2 | 19 / 3 / 6 / 1 | 23 / 1 / 5 / 0 |

## Casos de control

Series con comportamiento conocido (`taxonomia/control.yaml`). Si no tienen datos utilizables, no sirven para sanear el método.

| Esperado | Nodo | CO | MX | ES |
|---|---|---|---|---|
| pico | `estilo.barbiecore` | sin_datos | sin_datos | sin_datos |
| pico | `estampado.tie_dye` | apta_senal | apta_senal | apta_backtest |
| pico | `estilo.cottagecore` | apta_senal | apta_backtest | apta_senal |
| pico | `estilo.mob_wife` | insuficiente | insuficiente | insuficiente |
| alza | `prenda.pantalon_cargo` | apta_senal | apta_senal | apta_senal |
| alza | `corte.baggy` | apta_backtest | apta_backtest | apta_backtest |
| alza | `corte.pierna_ancha` | insuficiente | apta_backtest | apta_senal |
| baja | `corte.skinny` | apta_senal | apta_backtest | apta_senal |
| estacional | `prenda.traje_bano` | apta_backtest | apta_backtest | apta_backtest |
| estacional | `prenda.abrigo` | apta_backtest | apta_backtest | apta_backtest |
| estacional | `tela.lana` | apta_backtest | apta_backtest | apta_backtest |
| estable | `prenda.camiseta` | apta_backtest | apta_backtest | apta_backtest |
| estable | `tela.algodon` | apta_backtest | apta_backtest | apta_backtest |

## Nodos por revisar

Nodos sin datos o insuficientes en un mercado: candidatos a cambiar de consulta (el problema suele ser la consulta, no la tendencia).

### CO (57)

- `prenda.capri` — «pantalón capri» — insuficiente (media36 0.0, 265 meses útiles)
- `prenda.conjunto` — «conjunto dos piezas» — insuficiente (media36 1.0, 189 meses útiles)
- `corte.recto` — «jean recto» — insuficiente (media36 4.9, 57 meses útiles)
- `corte.pierna_ancha` — «jean pierna ancha» — insuficiente (media36 0.1, 245 meses útiles)
- `corte.bota_ancha` — «jean bota ancha» — insuficiente (media36 19.2, 93 meses útiles)
- `corte.tiro_bajo` — «tiro bajo» — insuficiente (media36 14.7, 81 meses útiles)
- `corte.entallado` — «entallado» — insuficiente (media36 0.0, 125 meses útiles)
- `corte.asimetrico` — «vestido asimétrico» — insuficiente (media36 0.0, 230 meses útiles)
- `corte.sastreria` — «traje sastre» — insuficiente (media36 31.3, 161 meses útiles)
- `corte.plisado` — «plisado» — insuficiente (media36 2.0, 217 meses útiles)
- `corte.cut_out` — «cut out» — insuficiente (media36 1.5, 158 meses útiles)
- `corte.cuello_alto` — «cuello alto» — insuficiente (media36 4.1, 260 meses útiles)
- `corte.manga_globo` — «manga globo» — insuficiente (media36 0.0, 255 meses útiles)
- `corte.hombros_descubiertos` — «hombros descubiertos» — insuficiente (media36 8.1, 131 meses útiles)
- `tela.algodon_organico` — «algodón orgánico» — sin_datos (sin_datos)
- `tela.algodon_pima` — «algodón pima» — sin_datos (sin_datos)
- `tela.cuero_vegano` — «cuero vegano» — insuficiente (media36 0.4, 215 meses útiles)
- `tela.viscosa` — «viscosa» — insuficiente (media36 0.9, 160 meses útiles)
- `tela.franela` — «franela» — insuficiente (media36 4.1, 267 meses útiles)
- `tela.reciclada` — «tela reciclada» — insuficiente (media36 0.0, 113 meses útiles)
- `tela.tencel` — «tencel» — insuficiente (media36 2.8, 29 meses útiles)
- `tela.alpaca` — «alpaca» — insuficiente (media36 16.2, 161 meses útiles)
- `tela.fibras_naturales` — «fibras naturales» — insuficiente (media36 2.0, 271 meses útiles)
- `tela.tecnica` — «tela dry fit» — insuficiente (media36 2.5, 124 meses útiles)
- `tela.organza` — «organza» — insuficiente (media36 21.3, 179 meses útiles)
- `color.azul_petroleo` — «azul petróleo» — insuficiente (media36 20.2, 188 meses útiles)
- `color.azul_electrico` — «azul eléctrico» — insuficiente (media36 0.0, 124 meses útiles)
- `color.verde_salvia` — «verde salvia» — insuficiente (media36 5.0, 2 meses útiles)
- `color.mantequilla` — «amarillo mantequilla» — insuficiente (media36 0.0, 223 meses útiles)
- `color.borgona` — «borgoña» — insuficiente (media36 30.5, 81 meses útiles)
- `color.lavanda` — «lavanda» — insuficiente (media36 4.6, 131 meses útiles)
- `estampado.floral` — «estampado floral» — insuficiente (media36 0.0, 215 meses útiles)
- `estampado.vichy` — «gingham» — insuficiente (media36 0.0, 90 meses útiles)
- `estampado.tartan` — «tartán» — insuficiente (media36 0.0, 220 meses útiles)
- `estampado.geometrico` — «estampado geométrico» — sin_datos (sin_datos)
- `estampado.abstracto` — «estampado abstracto» — sin_datos (sin_datos)
- `estampado.lunares` — «lunares» — insuficiente (media36 3.2, 229 meses útiles)
- `estampado.tropical` — «estampado tropical» — sin_datos (sin_datos)
- `estampado.grafico` — «estampado gráfico» — insuficiente (media36 2.8, 46 meses útiles)
- `estilo.athleisure` — «athleisure» — insuficiente (media36 2.8, 22 meses útiles)
- `estilo.vintage` — «ropa vintage» — insuficiente (media36 20.9, 173 meses útiles)
- `estilo.segunda_mano` — «ropa de segunda mano» — insuficiente (media36 13.1, 85 meses útiles)
- `estilo.y2k` — «y2k» — insuficiente (media36 3.7, 263 meses útiles)
- `estilo.retro` — «ropa retro» — insuficiente (media36 11.8, 174 meses útiles)
- `estilo.preppy` — «preppy» — insuficiente (media36 2.8, 239 meses útiles)
- `estilo.grunge` — «grunge» — insuficiente (media36 0.2, 268 meses útiles)
- `estilo.coquette` — «coquette» — insuficiente (media36 6.4, 261 meses útiles)
- `estilo.balletcore` — «balletcore» — insuficiente (media36 0.0, 209 meses útiles)
- `estilo.gorpcore` — «gorpcore» — insuficiente (media36 0.0, 102 meses útiles)
- `estilo.quiet_luxury` — «quiet luxury» — insuficiente (media36 0.0, 90 meses útiles)
- `estilo.dark_academia` — «dark academia» — insuficiente (media36 0.0, 232 meses útiles)
- `estilo.barbiecore` — «barbiecore» — sin_datos (sin_datos)
- `estilo.normcore` — «normcore» — insuficiente (media36 0.0, 262 meses útiles)
- `estilo.sostenible` — «moda sostenible» — insuficiente (media36 0.0, 91 meses útiles)
- `estilo.mob_wife` — «mob wife» — insuficiente (media36 5.0, 32 meses útiles)
- `estilo.clean_girl` — «clean girl» — insuficiente (media36 0.0, 259 meses útiles)
- `estilo.utilitario` — «estilo utilitario» — insuficiente (media36 0.0, 185 meses útiles)

### MX (35)

- `prenda.capri` — «pantalón capri» — insuficiente (media36 29.0, 76 meses útiles)
- `corte.asimetrico` — «vestido asimétrico» — insuficiente (media36 7.1, 203 meses útiles)
- `corte.manga_globo` — «manga globo» — insuficiente (media36 15.8, 80 meses útiles)
- `tela.algodon_organico` — «algodón orgánico» — sin_datos (sin_datos)
- `tela.algodon_pima` — «algodón pima» — insuficiente (media36 2.8, 9 meses útiles)
- `tela.cuero_vegano` — «piel vegana» — insuficiente (media36 2.8, 54 meses útiles)
- `tela.viscosa` — «viscosa» — insuficiente (media36 17.7, 186 meses útiles)
- `tela.reciclada` — «tela reciclada» — insuficiente (media36 0.0, 61 meses útiles)
- `tela.tencel` — «tencel» — insuficiente (media36 4.9, 60 meses útiles)
- `tela.alpaca` — «alpaca» — insuficiente (media36 1.7, 261 meses útiles)
- `color.azul_electrico` — «azul eléctrico» — insuficiente (media36 20.3, 132 meses útiles)
- `color.verde_salvia` — «verde salvia» — insuficiente (media36 1.8, 248 meses útiles)
- `color.mantequilla` — «amarillo mantequilla» — insuficiente (media36 3.0, 217 meses útiles)
- `estampado.floral` — «estampado floral» — insuficiente (media36 26.3, 90 meses útiles)
- `estampado.vichy` — «gingham» — insuficiente (media36 6.4, 69 meses útiles)
- `estampado.tartan` — «tartán» — insuficiente (media36 0.4, 203 meses útiles)
- `estampado.geometrico` — «estampado geométrico» — sin_datos (sin_datos)
- `estampado.abstracto` — «estampado abstracto» — insuficiente (media36 0.0, 150 meses útiles)
- `estampado.tropical` — «estampado tropical» — insuficiente (media36 0.0, 148 meses útiles)
- `estampado.camuflado` — «camuflado» — insuficiente (media36 22.6, 148 meses útiles)
- `estampado.grafico` — «estampado gráfico» — insuficiente (media36 0.0, 207 meses útiles)
- `estilo.athleisure` — «athleisure» — insuficiente (media36 15.7, 186 meses útiles)
- `estilo.segunda_mano` — «ropa de segunda mano» — insuficiente (media36 13.2, 160 meses útiles)
- `estilo.retro` — «ropa retro» — insuficiente (media36 3.9, 251 meses útiles)
- `estilo.coquette` — «coquette» — insuficiente (media36 6.8, 33 meses útiles)
- `estilo.balletcore` — «balletcore» — insuficiente (media36 0.2, 230 meses útiles)
- `estilo.gorpcore` — «gorpcore» — insuficiente (media36 0.0, 44 meses útiles)
- `estilo.quiet_luxury` — «quiet luxury» — insuficiente (media36 1.2, 183 meses útiles)
- `estilo.dark_academia` — «dark academia» — insuficiente (media36 0.0, 256 meses útiles)
- `estilo.barbiecore` — «barbiecore» — sin_datos (sin_datos)
- `estilo.normcore` — «normcore» — insuficiente (media36 0.1, 250 meses útiles)
- `estilo.sostenible` — «moda sostenible» — insuficiente (media36 2.3, 156 meses útiles)
- `estilo.mob_wife` — «mob wife» — insuficiente (media36 7.7, 32 meses útiles)
- `estilo.clean_girl` — «clean girl» — insuficiente (media36 2.4, 100 meses útiles)
- `estilo.utilitario` — «estilo utilitario» — insuficiente (media36 0.0, 145 meses útiles)

### ES (28)

- `prenda.capri` — «pantalón capri» — insuficiente (media36 16.2, 52 meses útiles)
- `corte.manga_globo` — «manga globo» — insuficiente (media36 14.8, 101 meses útiles)
- `corte.hombros_descubiertos` — «hombros al aire» — insuficiente (media36 1.8, 126 meses útiles)
- `tela.algodon_organico` — «algodón orgánico» — insuficiente (media36 7.7, 102 meses útiles)
- `tela.algodon_pima` — «algodón pima» — insuficiente (media36 0.0, 90 meses útiles)
- `tela.reciclada` — «tela reciclada» — insuficiente (media36 1.1, 171 meses útiles)
- `tela.tencel` — «tencel» — insuficiente (media36 37.2, 118 meses útiles)
- `tela.tecnica` — «tejido técnico» — insuficiente (media36 0.0, 162 meses útiles)
- `color.azul_petroleo` — «azul petróleo» — insuficiente (media36 6.8, 239 meses útiles)
- `color.verde_salvia` — «verde salvia» — insuficiente (media36 20.7, 67 meses útiles)
- `color.mantequilla` — «amarillo mantequilla» — insuficiente (media36 18.1, 26 meses útiles)
- `estampado.tartan` — «tartán» — insuficiente (media36 18.5, 179 meses útiles)
- `estampado.geometrico` — «estampado geométrico» — insuficiente (media36 0.0, 52 meses útiles)
- `estampado.abstracto` — «estampado abstracto» — insuficiente (media36 1.8, 173 meses útiles)
- `estampado.tropical` — «estampado tropical» — insuficiente (media36 0.3, 261 meses útiles)
- `estampado.camuflado` — «camuflado» — insuficiente (media36 6.5, 199 meses útiles)
- `estampado.grafico` — «estampado gráfico» — sin_datos (sin_datos)
- `estilo.athleisure` — «athleisure» — insuficiente (media36 14.7, 123 meses útiles)
- `estilo.balletcore` — «balletcore» — insuficiente (media36 0.0, 193 meses útiles)
- `estilo.gorpcore` — «gorpcore» — insuficiente (media36 1.6, 249 meses útiles)
- `estilo.quiet_luxury` — «quiet luxury» — insuficiente (media36 2.8, 3 meses útiles)
- `estilo.dark_academia` — «dark academia» — insuficiente (media36 2.1, 246 meses útiles)
- `estilo.barbiecore` — «barbiecore» — sin_datos (sin_datos)
- `estilo.normcore` — «normcore» — insuficiente (media36 0.4, 239 meses útiles)
- `estilo.sostenible` — «moda sostenible» — insuficiente (media36 9.6, 127 meses útiles)
- `estilo.mob_wife` — «mob wife» — insuficiente (media36 8.5, 32 meses útiles)
- `estilo.clean_girl` — «clean girl» — insuficiente (media36 2.8, 7 meses útiles)
- `estilo.utilitario` — «estilo utilitario» — sin_datos (sin_datos)
