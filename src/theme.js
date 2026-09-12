// Tema "Family" (moda): canvas crema + tarjetas blancas con borde interior
// en vez de sombra. Los colores viven como custom properties para no
// duplicar estilos. El acento (ember) y los tres estados de decisión son
// los únicos colores con peso — el resto de la interfaz se queda callada.
export const palette = {
  paper: "var(--paper)",
  card: "var(--card)",
  sand: "var(--sand)",
  ink: "var(--ink)",
  inkSoft: "var(--ink-soft)",
  line: "var(--line)",
  lineSoft: "var(--line-soft)",
  rust: "var(--accent)",
  olive: "var(--pos)",
  mustard: "var(--warn)",
  neg: "var(--neg)",
};

export const FONT = {
  display: "'Oswald', 'Arial Narrow', sans-serif",
  ui: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  mono: "'IBM Plex Mono', ui-monospace, monospace",
};

export const THEME_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

  /* Solo modo claro, a propósito — el sistema de referencia (Family) define
     un único mundo visual y no tiene sentido inventarle una versión oscura. */
  .radar {
    --paper: #FBFAF9;
    --card: #FFFFFF;
    --sand: #F6F4EF;
    --ink: #343433;
    --ink-soft: #7E7E7D;
    --line: #F2F0ED;
    --line-soft: #F2F0ED;
    --stitch: #E5D5C3;
    --accent: #FF3E00;
    --pos: #0A7A34;
    --pos-bg: #E4FBEA;
    --warn: #8A5C00;
    --warn-bg: #FFF1D6;
    --neg: #C21C28;
    --neg-bg: #FFE3E3;
    color-scheme: light;
  }

  .radar { scroll-behavior: smooth; }
  .radar * { box-sizing: border-box; }
  .radar [id] { scroll-margin-top: 68px; }
  .radar ::selection { background: var(--accent); color: #fff; }
  .radar :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }

  /* Tarjetas: sin sombra — el borde vive adentro, como una hoja pegada al papel */
  .card-flat {
    background: var(--card);
    box-shadow: inset 0 0 0 1px var(--line);
    border-radius: 10px;
    transition: background-color .15s ease;
  }
  .card-flat:hover { background: var(--sand); }
  .card-tap { text-align: left; width: 100%; }

  .hairline { border-top: 1px solid var(--line); }
  /* Pespunte: divisor punteado que separa lo cualitativo (nombre, decisión)
     de lo cuantitativo (momentum, código) dentro de una misma tarjeta —
     como el hilo visible de una costura real. */
  .stitch { border-top: 1px dashed var(--stitch); }
  .num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }

  /* Tag de muestra de tela: prendido a la tarjeta como un cartón de color
     físico, con el puntito del hilo. */
  .tag {
    position: absolute; top: -10px; left: 18px; width: 30px; height: 30px;
    border-radius: 6px; transform: rotate(-3deg);
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
  }
  .tag::after {
    content: ""; position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
    width: 5px; height: 5px; border-radius: 50%; background: var(--card);
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.14);
  }
  .cat-label {
    font-family: ${FONT.mono}; font-size: 10px; letter-spacing: .14em;
    text-transform: uppercase; color: var(--ink-soft); margin: 8px 0 8px;
  }

  .chip {
    display: inline-flex; align-items: center; gap: 5px;
    font-family: ${FONT.ui}; font-weight: 600; font-size: 11px; letter-spacing: -0.005em;
    padding: 4px 10px; border-radius: 999px; border: none;
    color: var(--ink-soft); background: var(--line); white-space: nowrap;
  }
  .chip-dot { width: 5px; height: 5px; border-radius: 999px; flex: none; }

  .navlink {
    font-family: ${FONT.ui}; font-size: 12px; color: var(--ink-soft);
    padding: 4px 0; border-bottom: 1px solid transparent; transition: color .15s, border-color .15s;
  }
  .navlink:hover { color: var(--ink); border-bottom-color: var(--ink); }

  @media (prefers-reduced-motion: reduce) {
    .radar *, .radar *::before { transition: none !important; animation: none !important; }
  }
`;
