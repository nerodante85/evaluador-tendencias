# Qué cuenta como "tendencia sostenida"

Sin esta definición el backtesting es circular: cualquier modelo parece bueno si el criterio de acierto se ajusta después de ver los resultados. Estos parámetros quedan fijados **antes** de ajustar ningún modelo. Si hay que cambiarlos, el cambio se anota abajo con fecha y motivo, y el backtesting se repite completo.

**Qué mide.** Interés de búsqueda relativo (Google Trends, 0–100, mensual), no ventas. Un acierto aquí significa "el interés de búsqueda se comportó como se proyectó". La verdad de terreno sobre demanda real solo llegará con datos de ventas (fase 7).

## Ventanas

Para un corte `T` (último mes conocido) y un horizonte `H` (6, 12 o 24 meses):

- **Base `B`** = media de los 12 meses que terminan en `T`.
- **Futuro `F`** = media de los 12 meses que terminan en `T + H`.
- Se usan siempre ventanas de 12 meses completos: así la estacionalidad se cancela sin necesidad de desestacionalizar.
- Denominador con piso de ruido: `B' = max(B, 5)`. Evita que una serie que sale de casi cero dé razones absurdas.

## Etiquetas

| Etiqueta | Condición (las tres a la vez) |
|---|---|
| **Alza sostenida** | `F / B' ≥ 1.25` · al menos 9 de los 12 meses futuros `≥ B` · `mediana(F) / B' ≥ 1.15` |
| **Baja sostenida** | `F / B' ≤ 0.75` · al menos 9 de los 12 meses futuros `≤ B` · `mediana(F) / B' ≤ 0.85` |
| **Pico de atención** | El mes máximo del futuro es `≥ 2 × B'` y no cumple la condición de persistencia (menos de 9 de 12 meses por encima de `B`) |
| **Estable** | Ninguna de las anteriores |
| **No evaluable** | `B < 5` y `F < 5`, o menos de 10 años de historia útil (ver abajo) |

La mediana y la persistencia son lo que separa una tendencia de un pico: un pico eleva la media pero no la mediana ni el número de meses por encima de la base.

## Historia útil

La historia útil de una serie empieza en el primer mes con valor `≥ 3` dentro de la primera ventana de 12 meses cuya media es `≥ 3` (antes de eso es ruido de bajo volumen y no cuenta como historia). Para entrar al backtesting una serie necesita al menos 120 meses (10 años) desde ahí, más una media de los últimos 36 meses `≥ 8` y no más de 10 % de meses en cero en los últimos 60. Los umbrales de "apta para señal" (menos exigentes) están en `pipeline/calidad.py`.

## Parámetros

| Parámetro | Valor | Nota |
|---|---|---|
| Umbral de crecimiento | +25 % / −25 % | Sensibilidad a probar: 15 %, 25 %, 40 % |
| Persistencia mínima | 9 de 12 meses | Sensibilidad: 8, 9, 10 |
| Piso de ruido | 5 | En la escala propia de cada serie |
| Horizontes | 6, 12, 24 meses | |
| Ventana | 12 meses | |

El backtesting reportará los resultados para el valor central **y** para los valores de sensibilidad. Si las conclusiones cambian según el umbral, eso es un hallazgo y se reporta como tal.

## Casos de control

Series con un comportamiento conocido, para verificar que las etiquetas hacen lo que dicen. Son hipótesis para sanear el método, **no** verdad de terreno: lo que salga de los datos manda.

| Comportamiento esperado | Nodos |
|---|---|
| Moda pasajera (pico) | `estilo.barbiecore`, `estampado.tie_dye`, `estilo.cottagecore`, `estilo.mob_wife` |
| Alza sostenida | `prenda.pantalon_cargo`, `corte.baggy`, `corte.pierna_ancha` |
| Baja sostenida | `corte.skinny` |
| Estacional | `prenda.traje_bano`, `prenda.abrigo`, `tela.lana` |
| Estable | `prenda.camiseta`, `tela.algodon` |

Están listados en `taxonomia/control.yaml` y el informe de calidad verifica que cada uno tenga datos utilizables.

## Cambios a esta definición

_(ninguno todavía)_
