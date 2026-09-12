# Criterios de decisión de colección y lista de materiales (2026–2027)

Panel visual: https://claude.ai/code/artifact/6d8f5360-033e-4ac3-90f5-7d75d3c6a1fb

Contexto: taller propio de confección; segmentos mujer, hombre y unisex/streetwear; plan anual.

## Seis factores además de la tendencia
1. **Desfase pasarela → vitrina local**: 12–24 meses. El panel de Google Trends sirve para detectar el momento en que la señal global empieza a confirmarse localmente.
2. **Clima**: Colombia no tiene FW. Del calendario internacional se toma silueta y color, no peso de tela. El calendario que manda es comercial (madres, regreso a clases, primas, Navidad).
3. **Costo real**: tela + desperdicio de trazo (8–15%) + insumos + confección + empaque + merma. Estampados direccionales y cuadros suben el consumo 10–20%.
4. **Capacidad del taller**: máximo dos materiales verdaderamente nuevos por colección.
5. **Riesgo de inventario**: color de tendencia en rollos cortos; color base en volumen. Preferir telas que sirvan a 3+ referencias.
6. **Identidad de marca**: Colombiamoda 2026 puso identidad, artesanía y sostenibilidad como eje. Elegir 2–3 señales y llevarlas a fondo.

## Filtro de 5 preguntas por señal
¿Sube local o solo global? ¿Cabe en el clima y uso real? ¿Existe la tela en el mercado nacional a volumen comprable? ¿Sirve a más de una referencia? ¿Se puede probar con 20–30 unidades?

## Dónde vender: variación regional y de canal
La misma prenda no tiene demanda pareja en toda la zona de venta — el mapa importa tanto como la tela. Antes de fijar la cantidad total de una referencia:
- Correr `fetch_trends.py` cambiando el parámetro `geo` (CO nacional vs. frontera/VE, u otras zonas si Google Trends lo permite a nivel subnacional) para ver si una señal sube pareja o está concentrada en una región.
- Registrar sell-through por región/canal y no solo por referencia y color (ver "Métricas a registrar" abajo) — hoy es el dato que falta para decidir mezcla de tallas y cantidad por punto de venta o canal (tienda física, feria, mayorista).
- Antes de repartir unidades entre puntos de venta, preguntar: ¿esta pieza vende igual en frontera que en el resto de la zona? ¿el canal cambia el mix de tallas o solo la cantidad?
- Una vez haya 2-3 temporadas de este dato acumulado, es viable estimar la curva de talla/mix de una referencia nueva buscando las referencias más parecidas ya vendidas en esa misma región (ver evaluación de "vecinos similares" en `claude/evaluacion-lexi-funcionalidades.md`).

## Estructura de presupuesto de telas
- 60% núcleo · 30% tendencia confirmada · 10% apuesta

**Núcleo**: jersey algodón 180–200 g (0,9–1,1 m/prenda) · denim 10–12 oz con elastano (1,5–1,7 m) · twill/drill 240–280 g (1,4–1,6 m) · popelina/oxford 120–140 g (1,6–1,8 m) · french terry 280–320 g (1,6–1,9 m).

**Tendencia**: lino y mezcla lino-algodón · algodón orgánico certificado · reciclados (rPET / algodón reciclado) · gabardina liviana de sastrería (blazer largo, 1,8–2,2 m) en borgoña, azul petróleo, oliva.

**Apuesta**: cuadros gingham/Príncipe de Gales · animal print sutil · punto en fucsia eléctrico o naranja energía (máx. 30 unidades de prueba).

**Insumos**: hilos por carta de color, cierres (metálico #4.5 denim, invisible, plástico #5), botones/herrajes mate y corozo, entretelas con prueba de encogimiento, elásticos y cordones, marquilla + etiqueta de composición + empaque reciclable, accesorios (cinturones, bolsos grandes) como categoría de margen alto.

## Contexto macro relevante
- Algodón: futuros NY cayeron de 88 a ~72 ¢/lb (may–jun 2026) pero inventarios finales proyectados −5,5 M pacas → conviene asegurar precio en la compra grande de fin de 2026.
- Arancel del 40% a confección importada bajo US$10/kg: protege al confeccionista pero encarece insumos importados. Tener siempre alternativa nacional identificada.
- Consumidor SS27 en "placer contenido": exige valor tangible, favorece el argumento de hechura.

## Métricas a registrar
Sell-through a 8 semanas por referencia, color **y región/canal** · metros sobrantes por tela (>15% = error de compra) · costo real vs. presupuestado · tiempo de confección por referencia.

**Siguiente paso sugerido**: agregar al panel dos columnas por señal — "¿la compré?" y "sell-through obtenido" — para calibrar qué fuentes aciertan en este mercado. Sumar región/canal a esas columnas en cuanto exista ese dato (ver sección "Dónde vender" arriba).
