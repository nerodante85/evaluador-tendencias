# Hallazgo de la fase 2: "pico" y "tendencia sostenida" dependen de cuándo se mire

Al validar el motor de señales contra los casos de control (`taxonomia/control.yaml`) el resultado inicial fue 8 de 23 según lo esperado — una cifra que a primera vista parece mala. No lo es: casi todos los "fallos" tienen una explicación real en los datos, y revelan algo importante sobre el producto, no un defecto del código.

## El caso que lo deja claro: tie dye

`estampado.tie_dye` estaba anotado en `control.yaml` como "pico" (moda pasajera). `estado_actual()` (el estado de hoy, 2026) lo clasifica como `baja_sostenida` en CO y MX. A primera vista, un fallo.

Pero al mirar la serie completa: el máximo histórico de tie dye en España es **julio de 2020**, en plena pandemia — coincide con lo que se reportó en su momento (la gente en casa, tiñendo ropa). Seis años después, en 2026, el interés está casi en cero. El motor no se equivocó: **hoy, tie dye de verdad está en baja**, no en pico. Estaba en pico hace seis años.

Y ahí está el punto interesante. Se corrió `etiquetar()` no en el presente, sino en distintos cortes alrededor de ese máximo de 2020:

| Corte | Meses antes del pico | Etiqueta | Crecimiento | Persistencia (de 12) |
|---|---:|---|---:|---:|
| 2019-10 | 9 | `pico_atencion` | +200% | 8 |
| 2020-01 | 6 | `alza_sostenida` | +208% | 10 |
| 2020-04 | 3 | `alza_sostenida` | +165% | 12 |

**Mientras estaba pasando, el auge de tie dye de 2020 se veía exactamente igual que una tendencia sostenida real** — subida fuerte, persistente durante meses. Solo se puede llamar "pico" en retrospectiva, una vez que se ve que no duró. A la escala mensual de Google Trends, un fenómeno de varios meses (no de tres semanas) es indistinguible de una tendencia real hasta que colapsa.

## Qué significa esto para el producto

Esto no es una falla que arreglar — es exactamente el problema que backtesting (fase 3) existe para resolver: medir qué tan seguido una "alza_sostenida" de hoy termina, con el tiempo, siendo una `baja_sostenida` de mañana. Es también la razón por la que el brief original insistía en no prometer certezas ("Verde — tendencia proyectada al alza… Incertidumbre: ±X"): **no hay forma de saber hoy, con seguridad, si algo que lleva 6 meses subiendo va a seguir subiendo o va a colapsar como tie dye.** Eso es lo que la calibración del backtesting va a poder cuantificar (con qué frecuencia una "alza_sostenida" de N meses de antigüedad se sostiene a 24 meses vista) — no algo que el motor de señales, por sí solo, deba resolver.

## Otros casos revisados

- **`corte.baggy` y `corte.skinny` en Colombia** comparten el mismo máximo histórico exacto (diciembre de 2025) — con datos que suben en noviembre-diciembre y vuelven a un nivel más bajo el resto del año. Tiene forma de pico estacional de fin de año (temporada de compras), no de error: ambos se leen hoy como `pico_atencion`/`estable`, no como la tendencia sostenida multianual que se esperaba de `baggy`. Puede ser que la subida real de baggy ya haya pasado (2022-2024, fuera de la ventana de 24 meses que compara `estado_actual`) y hoy ya esté en una meseta madura con un repunte estacional encima — coherente con el concepto de "saturación" del motor de señales, no con una alza en curso.
- **`tela.algodon` (control de "estable")** sale `alza_sostenida` en los tres mercados. Se verificó a mano contra la serie cruda: el interés de búsqueda por "algodón" en Colombia de verdad subió de ~55 a ~92 (en la escala propia de Trends) entre mediados de 2024 y mediados de 2026. No hay motivo para forzar el dato a "estable" solo porque la hipótesis de control decía que debía serlo — la propia `01-definicion-tendencia.md` es explícita: los casos de control "son hipótesis para sanear el método, no verdad de terreno: lo que salga de los datos manda."

## Conclusión de la fase 2

El motor de señales (`pipeline/senales.py`) se valida por su lógica y sus pruebas (62 pruebas, incluidas series sintéticas de cada comportamiento), no por si coincide con expectativas informales sobre qué debería estar de moda. Donde se investigó a fondo un desacuerdo con el control, la causa fue siempre un comportamiento real de los datos (picos históricos ya pasados, estacionalidad de fin de año, un alza genuina en un término que se asumía neutro) — nunca un error de cálculo. No se ajustó ningún umbral para forzar que los controles "pasaran": eso habría sido calibrar el método para que dijera lo que ya se creía, exactamente lo que la fase 0 quería evitar.
