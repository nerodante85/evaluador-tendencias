# Solicitud de acceso — API alfa de Google Trends

Texto preparado para el formulario de developers.google.com/search/apis/trends (sección "Postúlate para convertirte en verificador del canal alfa"). El formulario pide iniciar sesión con una cuenta de Google antes de mostrar los campos, así que no se pudo ver la estructura exacta — este texto cubre lo que casi cualquier formulario de este tipo pide (quién eres, qué vas a construir, por qué la API oficial y no otra cosa, en qué etapa estás, qué feedback puedes dar) y se puede recortar o adaptar al campo específico que aparezca.

## Caso de uso (español)

> Estoy construyendo Radar 2.0, una herramienta de detección de tendencias de moda para empresarios de la confección y diseñadoras en Colombia, México y España. El objetivo es explicar por qué una tendencia está creciendo, qué tan consistente es y qué tan confiable es la proyección — no solo mostrar un número.
>
> Ya tengo un pipeline funcionando con una taxonomía de ~150 categorías de moda (prendas, cortes, telas, colores, estampados, estilos) por tres mercados, un motor que calcula crecimiento, persistencia, aceleración, volatilidad y estacionalidad de cada serie, un backtesting con modelos estadísticos (naive estacional, media móvil, Holt-Winters, SARIMA) validado con significancia estadística real contra series históricas, y un Trend Score calibrado con regresión logística. Todo esto corre hoy sobre `pytrends`, una librería no oficial que Google archivó en abril de 2025 y que puede dejar de funcionar sin aviso.
>
> Necesito la API oficial por dos razones concretas que la interfaz pública y las librerías no oficiales no resuelven:
>
> 1. **Comparar decenas de términos con escala consistente.** Mi taxonomía tiene ~150 términos por mercado; la interfaz de Trends solo compara 8 a la vez y normaliza cada consulta 0–100 por separado, así que no puedo comparar el nivel de interés entre categorías distintas — solo la forma de una misma serie en el tiempo. La API resuelve esto de raíz.
> 2. **Historia estable para backtesting.** Mi metodología corre el mismo modelo en cientos de puntos de corte históricos y compara contra lo que realmente pasó después. Necesito que esa historia no cambie de escala entre corridas.
>
> Puedo empezar a usar la API de inmediato — el pipeline, la taxonomía y el backtesting ya existen y están probados (con pruebas automatizadas y datos reales). Puedo dar feedback concreto: por ejemplo, encontré que filtrar por categoría "Ropa" suprime el volumen de términos de estética/tendencia como "cottagecore" o "tie dye" en mercados de habla hispana, mientras que sin ese filtro aparece volumen real — es el tipo de matiz que probablemente le sirva al equipo.
>
> El volumen esperado es modesto: unos cientos de consultas por corrida, una corrida cada una o dos semanas.

## Versión en inglés (por si el formulario o el equipo de revisión la prefiere)

> I'm building Radar 2.0, a fashion-trend detection tool for apparel manufacturers and designers in Colombia, Mexico, and Spain. The goal is to explain *why* a trend is growing, how consistent it is, and how reliable the projection is — not just surface a number.
>
> I already have a working pipeline: a taxonomy of ~150 fashion categories (garments, cuts, fabrics, colors, prints, styles) across three markets, a signal engine computing growth, persistence, acceleration, volatility, and seasonality per series, a backtesting framework (seasonal naive, moving average, Holt-Winters, SARIMA) validated with real statistical significance against historical data, and a logistic-regression-calibrated Trend Score. All of this currently runs on `pytrends`, an unofficial library Google archived in April 2025 that could stop working without notice.
>
> I need the official API for two concrete reasons the public UI and unofficial libraries can't solve:
>
> 1. **Comparing dozens of terms on a consistent scale.** My taxonomy has ~150 terms per market; the Trends UI only compares 8 at a time and normalizes each query 0–100 independently, so I can't compare interest levels across different categories — only the shape of a single series over time. The API solves this directly.
> 2. **Stable history for backtesting.** My methodology re-runs the same model at hundreds of historical cut points and compares against what actually happened next. I need that history to not rescale between runs.
>
> I can start using the API immediately — the pipeline, taxonomy, and backtesting already exist and are tested (automated tests, real data). I can give concrete feedback: for example, I found that filtering by the "Apparel" category suppresses volume for aesthetic/style terms like "cottagecore" or "tie dye" in Spanish-speaking markets, while removing that filter surfaces real volume — the kind of nuance the team likely wants to hear.
>
> Expected volume is modest: a few hundred queries per run, roughly one run every one to two weeks.

## Notas

- Ajusta el volumen esperado o la frecuencia si cambian.
- Si el formulario pide un link al proyecto y no quieres compartir el repositorio (todavía es público, ver `CLAUDE.md`), se puede describir sin enlazarlo.
- Si pide nombre de empresa/organización y prefieres no usar tu nombre personal, dime cómo quieres que aparezca.
