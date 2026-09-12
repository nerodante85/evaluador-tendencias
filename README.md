# Evaluador de Tendencias — Radar de compra de materiales

Panel que cruza 30 señales de moda (color, prenda, material) con datos reales de
Google Trends, contexto macro colombiano y Pinterest Predicts, y las traduce en
una recomendación concreta de qué telas comprar y en qué cantidad.

Mercado de referencia: taller de confección en Norte de Santander, ciclo 2026–2027.

---

## Los tres comandos que vas a usar

```bash
npm install          # una sola vez, la primera vez
npm run dev          # abre el panel en http://localhost:5173
npm run build        # compila a dist/ (lo mismo que hace GitHub Pages)
```

Para los datos:

```bash
pip install -r requirements.txt   # una sola vez

python fetch_trends.py            # ~10 min, trae las 30 señales de Google Trends
python fetch_macro.py             # ~5 seg, trae la TRM oficial
```

Los dos scripts escriben directo lo que el panel lee. **Ya no hay que copiar y
pegar nada en el `.jsx`**: corres el script, recargas el panel y ahí están los
datos nuevos.

## Cómo publicar un cambio

```bash
git add -A
git commit -m "Corrida de tendencias de noviembre"
git push
```

Eso es todo. GitHub Actions compila y publica en GitHub Pages solo
(`.github/workflows/deploy.yml`). El sitio queda en
`https://<tu-usuario>.github.io/evaluador-tendencias/` unos dos minutos después.

> **Antes del primer push**, en el repositorio de GitHub: *Settings → Pages →
> Source* debe estar en **GitHub Actions** (no en "Deploy from a branch").

---

## Cómo está organizado

```
├── fetch_trends.py          Google Trends -> src/data/trends.json
├── fetch_macro.py           TRM oficial   -> src/data/macro.json
├── trends_config.json       LAS 30 SEÑALES: qué se mide y con qué término de búsqueda
│
├── src/
│   ├── data/
│   │   ├── trends.json      generado por fetch_trends.py — no editar a mano
│   │   ├── macro.json       generado por fetch_macro.py  — no editar a mano
│   │   ├── plan.json        telas, presupuesto, insumos, calendario, criterios (A MANO)
│   │   └── contexto.json    algodón, IPC, arancel, ferias, Pinterest Predicts (A MANO)
│   ├── engine.js            el motor de puntaje: cómo se decide comprar o no
│   ├── Dashboard.jsx        solo la interfaz
│   └── theme.js             colores y tipografía
│
├── historial/               una foto por corrida, para medir si el radar acertó
├── docs/                    criterios, auditoría, estrategia y línea base
└── .github/workflows/       el despliegue automático
```

Cuatro archivos concentran todo lo que cambia con el tiempo, y cada uno tiene
dueño claro:

| Qué quieres cambiar | Archivo | Quién lo escribe |
|---|---|---|
| Agregar o quitar una señal del radar | `trends_config.json` | tú |
| Los números de las señales | `src/data/trends.json` | `fetch_trends.py` |
| La tasa de cambio | `src/data/macro.json` | `fetch_macro.py` |
| Telas, consumos, calendario, criterios | `src/data/plan.json` | tú |
| Algodón, IPC, arancel, ferias, Pinterest | `src/data/contexto.json` | tú |
| Cómo se calcula la recomendación | `src/engine.js` | tú (o Claude Code) |
| Cómo se ve el panel | `src/Dashboard.jsx` | tú (o Claude Code) |

## Agregar una señal nueva

1. Agrégala a `trends_config.json` con un `id` y un `code` que no existan, y con
   un `query` escrito como lo buscaría un cliente, no como lo llamas internamente.
2. Corre `python fetch_trends.py`.
3. Si la señal justifica una tela, agrega su `id` al campo `senales` de esa tela
   en `src/data/plan.json` — así el respaldo de la tela se recalcula solo en cada
   corrida.

El autodiagnóstico del panel (última sección) genera ese bloque de configuración
listo para pegar, a partir de las señales propias que marques ahí.

## Cómo decide el panel

Cada señal recibe de 0 a 100 puntos: confianza del dato (+5 a +40), momentum
(hasta +30), dirección (+15 si sube / −20 si baja), búsqueda relacionada en
Breakout (+15), corroboración independiente con Pinterest Predicts (+15), y
−10 si es señal temprana de Asia (−5 si es de LatAm) todavía sin confirmar aquí.
De ahí salen las cuatro decisiones: **Comprar**, **Probar en lote pequeño**,
**Monitorear**, **Evitar / dejar salir**.

Dos topes que no dependen del puntaje: confianza baja nunca pasa de "Monitorear",
y una señal que va bajando cae a "Evitar" salvo que traiga breakout y
corroboración de Pinterest a la vez. La lógica completa está en `src/engine.js`
y el panel muestra el desglose al tocar cualquier tarjeta.

## Límites que conviene tener presentes

- **El momentum de Google Trends es relativo, no absoluto.** Es válido comparar
  la misma señal en el tiempo; no es válido comparar el momentum de una señal
  contra el de otra como si fueran unidades equivalentes.
- **`pytrends` es una librería no oficial.** Google puede cambiar su API interna
  sin aviso y el script deja de funcionar. Corre temprano, no en la fecha límite.
- **Casi todas las señales de Colombia dan confianza baja.** No es un error: es
  el volumen de búsqueda real de un mercado de este tamaño.
- **El panel no reemplaza tu sell-through.** Ordena señales dispersas para que la
  conversación de compra empiece con datos; la decisión sigue siendo tuya.

## Documentos

- `docs/criterios-compra-materiales.md` — los seis factores, el filtro de cinco
  preguntas y la estructura de presupuesto, en prosa.
- `docs/auditoria-2026-09.md` — qué se revisó, qué se corrigió y qué sigue abierto.
- `docs/linea-base-septiembre-2026.md` — la corrida de septiembre y cómo compararla
  contra la de noviembre. **Este es el ejercicio pendiente más importante.**
- `docs/estrategia-comercializacion.md` — el plan para convertir esto en servicio.
- `docs/evaluacion-lexi-funcionalidades.md` — comparación contra el competidor.
- `docs/flujo-generacion-variantes.md` — generar variantes de diseño antes de cortar.
- `docs/conector-google-trends.md` — el README original del conector.
