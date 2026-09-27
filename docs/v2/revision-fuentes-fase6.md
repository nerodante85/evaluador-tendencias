# Fase 6 — revisión de acceso a nuevas fuentes

Puerta de esta fase (`docs/v2/plan.md`): "cada fuente supera su revisión de acceso y términos" antes de integrarla al pipeline de la taxonomía. La revisión dio **negativo para las tres fuentes evaluadas hasta ahora** — con evidencia real, no una suposición — y eso es un resultado válido, no un fracaso: es exactamente para lo que existe esta puerta.

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

## MercadoLibre — descartada: la API bloquea estos endpoints incluso con app registrada y token válido

**Actualización (2026-09-27, con token real):** Ricardo registró la app en el DevCenter (`Client ID 1893963677539756`, scopes de solo lectura, sin tópicos) y completó el flujo OAuth completo (Authorization Code) hasta obtener un access token válido. Con ese token real:

```
GET /trends/MCO      -> 403 {"blocked_by":"PolicyAgent","code":"PA_UNAUTHORIZED_RESULT_FROM_POLICIES",
                             "message":"At least one policy returned UNAUTHORIZED."}
GET /sites/MCO/search?q=jean            -> el mismo 403
GET /sites/MCO/search?q=chaqueta cuero  -> el mismo 403
GET /sites/MCO/search?q=crop top        -> el mismo 403
```

Esto es distinto al 403 sin token de la primera ronda: el token sí es válido (si no lo fuera, el error sería 401 `invalid_token`, no este). El bloqueo lo pone un componente adicional de MercadoLibre ("PolicyAgent") **después** de validar el OAuth — una capa de autorización de negocio, no de autenticación.

No es un caso aislado: se encontró un reporte de otro desarrollador con el mismo síntoma exacto — un token que funciona contra `/users/me` pero recibe 403 en `/sites/MLB/search` — y notas de que, desde 2025, MercadoLibre restringió el acceso a búsqueda pública para aplicaciones nuevas registradas por el flujo estándar del DevCenter; el acceso real parece requerir un nivel de integración ("certificación") que normalmente se obtiene teniendo tráfico real de un vendedor en producción, no un registro de consulta como el nuestro.

**Conclusión: descartada, igual que Pinterest Trends.** No es un error de configuración recuperable desde este lado — es una puerta que MercadoLibre no abre para este tipo de uso. No tiene sentido invertir más tiempo en el adaptador (`pipeline/fuentes/mercadolibre.py` queda escrito y probado en vivo, sin conectar, por si algún día MercadoLibre habilita esto para integradores certificados). Sumado a que MercadoLibre tampoco opera en España, esta fuente como mucho hubiera aportado a 2 de los 3 mercados — ahora ni eso.

### Lo que se sabía antes de tener el token (para el registro histórico)

Se probó en vivo el endpoint de tendencias (`/trends/MCO`) y el de búsqueda de productos (`/sites/MCO/search`), ambos sin autenticación: **los dos devolvieron 403 Forbidden.** MercadoLibre exige hoy una aplicación registrada (client ID/secret, vía su portal de desarrolladores) incluso para búsquedas básicas — ya no es de acceso libre como se documentó como posibilidad en la fase 0.

Registrar una aplicación de desarrollador implica usar una cuenta de MercadoLibre y aceptar sus términos — eso es una decisión de Ricardo, no algo para hacer por cuenta propia. Se revisó la guía oficial ("Crea una aplicación en Mercado Libre") para dejar claro qué pide exactamente, sin necesidad de iniciar sesión para verlo:

### Lo que pide, paso a paso

1. **Una cuenta de MercadoLibre.** La guía recomienda explícitamente que sea "la cuenta del propietario de la solución" y que se cree "bajo una entidad legal" — es decir, piensan en esto como una cuenta de negocio, no una personal de comprador. Es tu decisión si usas una cuenta existente o creas una nueva para esto.
2. **Entrar a "Mis aplicaciones" (DevCenter)** con esa cuenta y hacer clic en "Crear nueva aplicación".
3. **Datos obligatorios del formulario:**
   - Nombre (único).
   - Descripción — máximo 150 caracteres, se le muestra al usuario cuando la app pide autorización. Sugerencia ya redactada: *"Radar de tendencias de moda: consulta datos públicos de búsqueda y catálogo en Colombia, México y España para análisis de mercado."* (130 caracteres).
   - Logo de la empresa (con dimensiones específicas que pide el formulario).
   - **URI de redirect — debe ser HTTPS.** Este proyecto no tiene servidor propio, pero el sitio de GitHub Pages ya sirve por HTTPS: una URL como `https://nerodante85.github.io/evaluador-tendencias/` alcanza como redirect URI técnicamente válido (el flujo de OAuth solo necesita que el navegador aterrice ahí con un código en la URL, que se copia a mano para el script — no hace falta que la página "haga" nada con ese código).
   - Scopes: pedir solo **Lectura** (GET) — esto es de solo consulta, no hace falta Escritura (PUT/POST/DELETE).
   - Tópicos (notificaciones push de Ordenes/Mensajes/etc.): no aplican, se pueden dejar sin marcar — son para vendedores que reciben pedidos, no para este uso.
4. Al guardar, entrega **Client ID y Secret Key** — con eso se arma el adaptador (`pipeline/fuentes/mercadolibre.py`, todavía no escrito).
5. En algunos países (Argentina, México, Brasil, Chile — Colombia no aparece en esa lista en la guía) piden validar que los datos de la cuenta coincidan con el titular antes de dejar crear la aplicación.

Nada de esto se hizo — es exactamente el punto donde se necesita tu cuenta y tu decisión. Si decides seguir, con el Client ID y Secret Key ya se puede escribir el adaptador siguiendo el mismo patrón de `pipeline/fuentes/trends.py` y `wikipedia.py`.

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
2. ¿Ya se definió presupuesto para un proveedor de pago, o sigue en pausa?

(MercadoLibre y Pinterest Trends ya no están en esta lista — las dos se descartaron con evidencia real: la primera por una política de la API que bloquea estos endpoints incluso con token válido, la segunda por la forma del dato. Ninguna necesita una decisión tuya.)
