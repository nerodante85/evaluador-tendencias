# Conector Google Trends — Radar de tendencias Conecta Moda

> Este era el `README.md` del proyecto de Claude. Se conserva como referencia del método.
> Las instrucciones de operación actualizadas (ahora que el panel es una app que corre local
> y se publica en GitHub Pages) están en el `README.md` de la raíz del repositorio.

Conecta las 14 señales del panel a datos reales de búsqueda en Google Trends.

## 1. Instalar (una sola vez)

Necesitas Python 3 instalado. Luego, en una terminal:

```bash
pip install pytrends
```

## 2. Correr

Con los tres archivos (`fetch_trends.py`, `trends_config.json`) en la misma carpeta:

```bash
python3 fetch_trends.py
```

Tarda unos 2-3 minutos (hace una pausa entre cada una de las 14 consultas para no
saturar a Google). Vas a ver en pantalla el progreso señal por señal.

## 3. Qué te entrega

- **trends_live.json** — todos los datos, por si quieres revisarlos o guardarlos
  como histórico.
- **trends_live.js** — el bloque `const TRENDS = [...]` ya listo para copiar y
  pegar dentro del archivo `.jsx` del panel, reemplazando el array actual.

## 4. Actualizar el panel

Dos formas:

- **Manual:** abre `trends_live.js`, copia el contenido, y pégamelo aquí en el
  chat pidiéndome que actualice el panel con esos datos.
- **Automática (siguiente paso, con n8n):** programa este mismo script para que
  corra cada 1-2 semanas y escriba el resultado en una Google Sheet o repositorio;
  ahí yo puedo leerlo cuando me pidas refrescar el panel.

## Notas importantes

- Google Trends **no tiene API oficial**. `pytrends` funciona simulando el
  navegador, así que puede fallar o bloquear temporalmente si lo corres muy
  seguido. Con correrlo 1 vez por semana es más que suficiente para esta
  categoría de decisiones.
- El **momentum** (0-100) es el interés de búsqueda relativo que reporta
  Google Trends para cada término en los últimos 12 meses — no representa
  ventas ni volumen absoluto de búsquedas.
- Puedes editar `trends_config.json` para: ajustar las consultas de búsqueda
  (`query`), agregar nuevas señales, o cambiar el `geo` (por ejemplo, `"VE"`
  para comparar con el lado venezolano de la frontera).

---

## Qué cambió desde que se escribió este documento

- El script pasó a la **v2** (24 meses de ventana, 30 señales, más `yoy`, `persistencia`,
  `volatilidad`, `volumen`, `estacional`, y guardado automático en `historial/`).
- El paso 4 (**copiar y pegar en el `.jsx`**) ya no existe: `fetch_trends.py` escribe
  directamente `src/data/trends.json`, que es lo que el panel lee. Los archivos
  `trends_live.json` / `trends_live.js` se siguen generando por compatibilidad.
