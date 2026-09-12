# Contexto para Claude Code

Repositorio del **Evaluador de Tendencias**: un radar de señales de moda que
termina en una recomendación de compra de telas. Lo usa Ricardo, consultor en
Cúcuta (Norte de Santander), para su propio taller y como base de un servicio que
quiere vender a empresas del clúster Conecta Moda.

El proyecto vivía como documentos y un artifact en Claude; el 2026-09-12 se
trasladó a este repositorio. Antes de trabajar acá, lee el `README.md`.

## Idioma

Todo — código, comentarios, commits, documentación, interfaz — va **en español**.
Los nombres de variables ya existentes mezclan español e inglés (`computeDecision`,
`respaldoTela`, `señales`); mantén el estilo del archivo que estés tocando en vez
de renombrar por consistencia.

## Qué toca cada cosa

- **`src/engine.js`** es el motor de decisión. Cambiar un peso aquí cambia todas
  las recomendaciones del panel. No lo toques "de paso" mientras haces otra cosa:
  si el cambio afecta el puntaje, dilo explícitamente.
- **`src/Dashboard.jsx`** es solo interfaz. Si estás cambiando cómo se ve, no
  debería hacer falta tocar `engine.js`.
- **`src/data/trends.json` y `src/data/macro.json` los escriben los scripts.**
  Nunca los edites a mano: la próxima corrida borra el cambio. Si hace falta
  corregir un dato de una señal, el arreglo va en `trends_config.json`.
- **`src/data/plan.json` y `src/data/contexto.json` son de Ricardo.** Son
  criterio editorial, no datos generados. Proponle los cambios, no los hagas por
  tu cuenta salvo que te lo pida.
- **`historial/`** es el registro de qué decía el radar en cada fecha. Es evidencia,
  no caché: nunca lo limpies ni lo reescribas.

## Cosas que no son bugs

- Casi todas las señales colombianas marcan `confianza: "baja"`. Es el volumen de
  búsqueda real de Colombia en Google Trends, no un fallo del cálculo.
- `computeDecision()` todavía **no** usa los campos `yoy`, `persistencia`,
  `volatilidad` ni `estacional` que trae la v2 del script. Ricardo decidió dejarlo
  para cuando haga falta. No lo "arregles" sin preguntar — cambia todos los
  puntajes del panel y rompería la comparación con la línea base de septiembre.
- El panel es solo modo claro, a propósito.
- `docs/` conserva documentos históricos con rutas viejas (`claude/panel-tendencias.jsx`).
  Son registro de lo que pasó; no actualices esas rutas.

## El compromiso abierto más importante

Comparar la corrida de septiembre de 2026 contra una de noviembre para medir si el
radar acertó. El método está en `docs/linea-base-septiembre-2026.md` y la foto de
septiembre en `historial/`. Es la evidencia que sostiene todo el plan comercial
(`docs/estrategia-comercializacion.md`): sin eso, no hay caso que mostrarle a un
cliente.

## Al publicar

El sitio es **público** desde el momento en que GitHub Pages está activo. El día
que entren datos de ventas de un cliente, esto deja de servir: toca repositorio
privado y despliegue con autenticación. Está anotado en
`docs/estrategia-comercializacion.md`; si ves que el trabajo va hacia allá,
recuérdalo antes de que se publique.

## Verificar antes de dar algo por terminado

```bash
npm run build     # tiene que pasar sin errores
npm run dev       # y hay que mirar el panel, no solo confiar en que compiló
```

Si tocaste un script de Python, córrelo de verdad: `fetch_macro.py` tarda segundos
y confirma que la escritura a `src/data/` sigue funcionando. `fetch_trends.py`
tarda ~10 minutos y golpea Google, así que no lo corras para probar un cambio
cosmético.
