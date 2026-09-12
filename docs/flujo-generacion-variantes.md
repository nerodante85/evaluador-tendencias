# Flujo: generar variantes de diseño antes de cortar tela

Implementa la funcionalidad #1 evaluada en `evaluacion-lexi-funcionalidades.md` (generación de conceptos antes de cortar). No requiere infraestructura nueva — usa ChatGPT o Gemini (las herramientas que ya usan tus clientes) más un script que arma los prompts en español a partir de tus propios datos de tendencias y materiales.

## Archivos
- `generar_prompts_diseno.py` — script que arma los prompts.
- `variantes_config.json` — las combinaciones silueta + color + material que quieres probar esta temporada (ejemplo con 3 entradas incluido).
- `trends_config.json` — el mismo archivo que ya usas con `fetch_trends.py` (debe estar en la misma carpeta).

## Cómo correrlo
1. Edita `variantes_config.json`: para cada combinación pon `referencia`, `silueta_code` y `color_code` (los códigos de `trends_config.json`, ej. `CM-26-P04`), `material` (texto libre — el script reconoce núcleo/tendencia/apuesta de `criterios-compra-materiales.md`) y `notas` de construcción si quieres. Máximo 2 materiales verdaderamente nuevos por colección, por la regla de capacidad del taller.
2. Corre `python3 generar_prompts_diseno.py` en esa carpeta.
3. Se generan dos archivos:
   - `prompts_variantes.md` — un prompt en español por combinación, listo para pegar en ChatGPT o Gemini, en formato "boceto técnico" (ficha técnica plana, sin modelo, sin marca) para que sirva como referencia de diseño real y no como foto editorial genérica.
   - `review_variantes.csv` — una tabla con las 5 preguntas del filtro del proyecto, vacía para que la llenes viendo cada imagen generada.
4. Pega cada prompt en ChatGPT o Gemini, guarda el resultado, y con la imagen en mano llena `review_variantes.csv`. La columna `decision` (probar / descartar / ajustar y repetir) es la que determina si esa combinación pasa a corte real.

## Próximo paso natural
Una vez se use un par de temporadas, `review_variantes.csv` empieza a ser el registro de qué combinaciones se probaron y con qué decisión — insumo directo para calibrar el filtro de 5 preguntas y, más adelante, para el catálogo estructurado que necesita la evaluación de embeddings (funcionalidad #3 de Lexi).

---

> **Nota al trasladar el proyecto a este repositorio (2026-09-12):** `generar_prompts_diseno.py` y `variantes_config.json` **no estaban guardados en el proyecto de Claude** — este documento los describe pero los archivos nunca se subieron. Si los tienes en tu máquina, cópialos a la raíz del repo; si no, hay que volver a escribirlos.
