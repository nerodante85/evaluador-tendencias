# Fase 6 — revisión de acceso a nuevas fuentes

Puerta de esta fase (`docs/v2/plan.md`): "cada fuente supera su revisión de acceso y términos" antes de integrarla al pipeline de la taxonomía. Esta vez la revisión dio **negativo para las dos fuentes gratuitas evaluadas** — con evidencia real, no una suposición — y eso es un resultado válido, no un fracaso: es exactamente para lo que existe esta puerta.

## Wikipedia Pageviews — acceso: sí. Integración automática: no.

**Lo que funciona:** la API (`wikimedia.org/api/rest_v1/metrics/pageviews`) es gratis, sin llave, sin registro. Se implementó y probó en vivo (`pipeline/fuentes/wikipedia.py`, 6 pruebas): pedir las vistas mensuales de un artículo real (`Denim`, `Crochet`, `Moda`) funciona sin problema.

**Por qué no se integró al pipeline de los 158 nodos de la taxonomía:**

1. **La búsqueda automática de artículos no sirve para moda.** Se probó `opensearch` de Wikipedia con términos reales de la taxonomía:

   | Búsqueda | Resultado que trajo Wikipedia | ¿Sirve? |
   |---|---|---|
   | streetwear | Streeterville, Street Arts, Burnett Hillman Streeter | No — ni un resultado real |
   | pantalón cargo | Pantalón corto, Pantalón corto de correr | No — encontró "pantalón", ignoró "cargo" |
   | jean bota ancha | (sin resultados) | No existe artículo |
   | crop top | Crop top | Sí, por suerte |

   De 4 búsquedas reales, solo 1 dio un resultado usable. Para que esto funcionara habría que curar a mano el título exacto de Wikipedia para cada nodo — el mismo trabajo editorial que ya llevó la taxonomía completa (`taxonomia/*.yaml`), no algo automatizable.

2. **Cuando el artículo sí existe, el volumen es bajo y ruidoso comparado con Trends.** Con datos reales de 2019-2024:

   | Artículo | Meses con dato | Mínimo | Máximo | Media |
   |---|---:|---:|---:|---:|
   | Denim | 61 | 0 | 233 | 118.8 |
   | Crochet | 61 | 0 | 80 | 41.9 |
   | Moda | 61 | 110 | 28.146 | 16.149.5 |

   Cientos de vistas al mes, en TODA la Wikipedia en español, para un concepto tan amplio como "Denim" — es un volumen mucho menor y más errático que el índice de Google Trends para la misma idea. Tiene sentido: Wikipedia es una referencia enciclopédica, no una herramienta de intención de compra o de búsqueda de tendencias.

3. **No hay forma de separar por país.** "es.wikipedia" mezcla lectores de España, México, Colombia y cualquier otro hispanohablante — esta fuente, si se llegara a usar, sería una sola señal "de habla hispana", no una por mercado como hoy da Trends. Rompería la comparación CO/MX/ES que es central al proyecto.

4. **El último mes suele venir incompleto** (mismo patrón "isPartial" que ya se maneja en Trends v1) — un detalle menor, resoluble, pero otro punto más de fricción.

**Conclusión:** el código queda listo y probado (`pipeline/fuentes/wikipedia.py`) para el día que tenga sentido usarlo, pero **no se conecta a `taxonomia/` ni a `pipeline/historia.py` todavía.** Sí podría valer la pena como un proyecto chico aparte: una lista curada a mano de ~15-20 conceptos amplios y bien establecidos (Denim, Moda, Streetwear si existe con otro título, etc.) — nunca para los ~150 nodos completos, la mayoría de los cuales (cortes específicos, estéticas de nicho) casi seguro no tienen artículo propio.

## MercadoLibre — ya no es pública, necesita decisión

Se probó en vivo el endpoint de tendencias (`/trends/MCO`) y el de búsqueda de productos (`/sites/MCO/search`), ambos sin autenticación: **los dos devolvieron 403 Forbidden.** MercadoLibre exige hoy una aplicación registrada (client ID/secret, vía su portal de desarrolladores) incluso para búsquedas básicas — ya no es de acceso libre como se documentó como posibilidad en la fase 0.

Registrar una aplicación de desarrollador implica usar una cuenta de MercadoLibre y aceptar sus términos — eso es una decisión de Ricardo, no algo para hacer por cuenta propia. Queda pendiente de tu decisión, no de una prueba técnica.

## Pinterest Trends API — descartada por la forma del dato, no solo por el acceso

Se investigó la API oficial de Pinterest (`trends_read`, endpoint `trending_keywords`), corroborado con la documentación oficial y con fuentes independientes coincidentes:

1. **Solo da el día de hoy — nunca fechas pasadas.** Cita textual encontrada: "Users are not able to retrieve trends for past dates, and API data is returned for today's date only." No hay forma de pedir una serie histórica por término, ni con acceso completo. Esto la descarta de raíz para el backtesting, que es la base de todo este pipeline — no es un problema de acceso, es que el dato no existe en la forma que se necesita.
2. **Es un top-50 del día, no una consulta por término.** La API devuelve los 50 términos que más están subiendo hoy en general — no se le puede preguntar "¿cómo ha ido 'pantalón cargo' este año?" como sí se le pregunta a Google Trends o a Wikipedia. Son dos formas de dato completamente distintas.
3. **Colombia no está entre los mercados que soporta.** Mercados confirmados: US, CA, GB+IE, DE, FR, IT, ES, MX, BR, AU+NZ, JP. De los tres mercados de Radar 2.0, **solo España y México están cubiertos — Colombia no.**
4. **Además, igual que MercadoLibre, requiere cuenta de negocio de Pinterest + app registrada + revisión de Pinterest** (con un proceso que en algunos casos pide hasta un video del flujo de OAuth) — otra decisión de cuenta/términos, no algo técnico para resolver por cuenta propia.

**No se construyó ningún adaptador.** A diferencia de Wikipedia (donde el código quedó listo para un futuro uso curado), aquí no hay nada que dejar listo: la API simplemente no puede alimentar el pipeline de series históricas por más acceso que se consiga.

Nota aparte para no confundir: esto es la API de **Pinterest Trends**, distinta de **Pinterest Predicts** (el reporte editorial anual que ya se usa a mano en `src/data/contexto.json` desde la v1) — ese reporte sigue siendo válido y no se toca, es contenido editorial anual, no un endpoint de datos.

## Lo que sigue sin tocar, sin cambios desde la fase 0

- **API oficial de Google Trends (alpha):** sigue esperando que Ricardo solicite acceso.
- **Proveedores de pago (SerpApi, DataForSEO, Glimpse):** sigue sin presupuesto definido.
- **Redes sociales:** sigue fuera de alcance (sin acceso legal).
- **Catálogos y pasarelas:** no se evaluaron en esta ronda.

## Decisión pendiente para Ricardo

1. ¿Vale la pena una lista curada a mano de ~15-20 conceptos amplios para Wikipedia, sabiendo que no separa por país y que el volumen es bajo? ¿O se deja en pausa?
2. ¿Quieres registrar una aplicación de desarrollador en MercadoLibre (con tu propia cuenta) para que se pueda evaluar su API de verdad?
3. ¿Ya se definió presupuesto para un proveedor de pago, o sigue en pausa?

(Pinterest Trends ya no está en esta lista — se descartó por la forma del dato, no necesita una decisión tuya.)
