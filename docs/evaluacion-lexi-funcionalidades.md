# Lexi (lexiapp.co) — comparación y evaluación de funcionalidades

_No pude abrir lexiapp.co directamente (error de servidor); esta nota se basa en la descripción de Ricardo, no en verificación directa del producto._

## El framework de Lexi vs. Evaluador de Tendencias
Lexi organiza la decisión de colección en tres preguntas. Frente a lo que ya existe en este proyecto:

| Pregunta de Lexi | Cobertura actual en Evaluador de Tendencias |
|---|---|
| Qué diseñar | Cubierta y más rigurosa: panel de 30 señales con fuente y momentum de Google Trends + filtro de 5 preguntas de viabilidad (no solo evidencia de demanda). |
| Cuánto producir | Parcial: existe la regla 60/30/10 y el tope de 20-30 unidades de prueba, pero no hay curva de tallas formalizada dentro de esa cantidad. |
| Dónde vender | Era el hueco real — se agregó una sección nueva en `criterios-compra-materiales.md` con el criterio de variación regional/canal. Falta el dato histórico para explotarla a fondo (ver punto 4 abajo). |

## Las cuatro funcionalidades a evaluar

### 1. Extractor de tendencias e imágenes de redes → señales accionables
**Qué hace:** monitorea redes sociales (imágenes/hashtags) y las convierte en señales de tendencia, similar a lo que hacen proveedores como Heuritech (que ya aparece como fuente en `trends_config.json`, vía prensa).

**Valor real para tu operación:** automatizaría la curación manual que hoy haces leyendo prensa especializada (Diario del Sur, El País, Harper's Bazaar México, etc.). El ahorro es de tiempo, no de calidad — tus fuentes actuales ya filtran señal de ruido antes de llegar a ti.

**Costo/complejidad:** alto. Requiere scraping de redes (frágil, contra términos de servicio) o un proveedor pago (Heuritech y similares cobran licencias pensadas para marcas grandes, no para un taller). Construirlo en casa con visión por computador es un proyecto de meses, no de una función más al panel.

**Recomendación: no construir esto.** Tu curación manual + Google Trends ya cumple la misma función a costo casi cero. Solo reconsiderar si el volumen de referencias a decidir crece mucho (ej. si empiezas a vender a otras marcas, no solo tu taller).

### 2. Embeddings / mapa vectorial del catálogo (comparar diseño nuevo vs. existente)
**Qué hace:** convierte cada prenda del catálogo en un vector (imagen + atributos) para medir qué tan parecido es un diseño nuevo a algo que ya vendes — detecta cannibalización o confirma que llena un vacío real.

**Valor real para tu operación:** encaja directo con tu propia regla "preferir telas/diseños que sirvan a 3+ referencias" — hoy esa evaluación la haces de memoria/visualmente. Automatizarla tiene sentido cuando el catálogo crece lo suficiente para que la memoria ya no alcance.

**Requisito bloqueante:** necesitas un catálogo fotografiado y con datos mínimos (tela, silueta, color, temporada) por referencia. Si eso no existe todavía como archivo ordenado, ese es el paso previo, no los embeddings.

**Costo/complejidad:** medio-bajo una vez el catálogo está digitalizado — hay modelos de embeddings de imagen (tipo CLIP) accesibles y baratos de correr; no requiere entrenar nada propio.

**Recomendación: prioridad media.** Vale la pena solo después de tener el catálogo fotografiado y estructurado. Si ese inventario ya existe, es la funcionalidad más barata de prototipar de las cuatro.

### 3. Generar diseños y variantes de conceptos antes de cortar tela
**Qué hace:** genera visualizaciones de silueta/color/tela combinados antes de invertir en un toile (muestra física).

**Valor real para tu operación:** alto — un toile mal calculado es tela y horas de confección perdidas; poder descartar combinaciones en una imagen generada antes de cortar reduce directamente ese riesgo, que tu propio documento ya identifica como el gasto más caro de la confección ("por si acaso").

**Costo/complejidad:** bajo-medio. No requiere infraestructura propia: se puede lograr hoy con herramientas de generación de imagen existentes, dándoles como referencia tus telas y siluetas reales. Es más un flujo de trabajo (prompt + tus fotos de tela) que un producto nuevo que construir.

**Recomendación: prioridad alta / la más fácil de probar ya.** De las cuatro, es la que menos depende de datos históricos que hoy no tienes — se puede pilotear con la próxima colección sin esperar nada.

### 4. Curva de talla y mix por región desde "vecinos similares" en el historial
**Qué hace:** para una referencia nueva, busca en el historial de ventas las referencias más parecidas (categoría, silueta, precio) y usa su curva de talla y mix regional real como estimador — un k-vecinos-más-cercanos clásico, no requiere IA compleja.

**Valor real para tu operación:** es la más alineada con los dos huecos reales de tu proceso: la curva de talla dentro de "cuánto producir" y la variación regional de "dónde vender" (la sección que se acaba de agregar a `criterios-compra-materiales.md`). Es también, técnicamente, la más simple de las cuatro — no necesita embeddings ni generación de imagen, solo un histórico limpio.

**Requisito bloqueante:** necesitas 2-3 temporadas de sell-through por referencia, talla **y** región/canal — ese dato hoy no existe como histórico estructurado (tu propio documento lo marca como "siguiente paso sugerido", aún no implementado).

**Recomendación: la de mayor prioridad a mediano plazo, pero hay que empezar por el dato, no por el modelo.** Sugerencia concreta: agregar ya las columnas de sell-through por región/canal (como quedó anotado en `criterios-compra-materiales.md`) para que dentro de 2-3 temporadas haya historial suficiente. El modelo de vecinos en sí se puede construir en un día una vez exista esa tabla.

## Orden de implementación sugerido
1. **Generación de variantes antes de cortar** — empezar ya, sin dependencias.
2. **Captura de datos por región/canal** (no es una "funcionalidad" de IA, es la base de datos) — empezar ya, para habilitar el punto 4 en 2-3 temporadas.
3. **Embeddings de catálogo** — cuando el catálogo esté fotografiado y estructurado.
4. **Curva de talla/mix por vecinos similares** — una vez haya historial suficiente del punto 2.
5. **Extractor de redes sociales** — no construir; tu curación manual + Google Trends ya cumple esa función a costo mucho menor para tu escala actual.
