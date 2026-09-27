# Hallazgo de la fase 4: dos pesos salen con el signo contrario al que asumía el brief

El brief original de la v2 proponía: `Trend Score = Crecimiento + Persistencia + Aceleración + ... − Saturación − Volatilidad` — saturación y volatilidad restando, por diseño. Calibrados contra datos reales (150 series × 10 cortes, target: ¿terminó en `alza_sostenida` a 24 meses?), los pesos salieron:

| Variable | Peso (multivariado) | Correlación marginal con "alza" |
|---|---:|---:|
| crecimiento | −0.088 (no significativo) | +0.108 |
| aceleración | −0.121 (no significativo) | +0.005 (~nula) |
| persistencia | **+0.432** (significativo) | +0.180 |
| **volatilidad** | **+0.305** (significativo) | +0.067 |
| **saturación** | +0.182 (apenas significativo) | +0.097 |

Dos hallazgos distintos, que conviene no confundir:

## `crecimiento` y `aceleración`: el signo se invierte por colinealidad, no por un efecto real

Solas, ambas variables correlacionan positivo (débil) con terminar en alza — lo esperable. Pero `crecimiento` está correlacionado 0.64 con `persistencia` y 0.62 con `aceleración` en esta muestra: son formas distintas de medir parte del mismo movimiento. Cuando las tres entran juntas al modelo, la regresión le da el crédito casi todo a `persistencia` (el predictor individual más fuerte) y a `crecimiento`/`aceleración` les queda un residuo que sale negativo — es el fenómeno estadístico estándar de coeficientes que cambian de signo bajo variables correlacionadas, no un hallazgo de que "crecer rápido hoy predice bajar mañana". El intervalo de confianza de ambas cruza el cero — el propio modelo dice que no hay evidencia sólida de que aporten algo, una vez que `persistencia` ya está en la ecuación.

## `volatilidad` y `saturación`: el signo positivo SÍ aparece incluso solas

A diferencia del caso anterior, estas dos correlacionan positivo con "alza" **incluso mirándolas solas**, sin las otras cuatro variables de por medio. No es un artefacto de colinealidad — es un patrón real en esta muestra, aunque débil (correlaciones de 0.067 y 0.097, nada fuerte). Dos lecturas posibles, ninguna descartable con esta evidencia:

1. **Una serie que ya viene de una base alta y errática** (más volatilidad, más cerca de su techo histórico) puede ser precisamente la que tiene más "material" para sostener una nueva alza — lo contrario de una serie plana y silenciosa, que no tiene de dónde subir.
2. **Ruido de una muestra todavía chica.** El intervalo de saturación casi toca cero (`[0.005, 0.359]`) — con más datos podría desaparecer.

Siguiendo la misma regla que en las fases 2 y 3: no se fuerza el signo a lo que el brief asumía. Lo que salió de los datos se reporta tal cual, con esta explicación, no se descarta ni se recalibra a mano para que "se vea como se esperaba".

## Qué hacer con esto

- El score queda como está — calibrado, documentado, con sus intervalos.
- **No se debería citar un peso individual (p. ej. "el 43% de la fórmula es persistencia") como si fuera una descomposición causal limpia.** Con esta colinealidad, eso sería engañoso. El score es útil como *un solo número que ordena señales*, no como una tabla de "por qué" que se pueda desglosar variable por variable con confianza.
- Antes de subir esto a producción, repetir con una muestra mayor (como se hizo en la fase 3) para ver si `volatilidad`/`saturación` mantienen el signo positivo o si era ruido de muestra.
