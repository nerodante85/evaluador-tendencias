// Tema "Radar Terminal": el panel se lee como un puesto de control nocturno
// para señales de moda — carbón cálido, datos en mono, un barrido de radar
// de verdad detrás del titular. La idea no es decoración: "Comprar/Probar/
// Monitorear/Evitar" ya se comporta como una señal de trading, así que el
// panel por fin se ve como lo que hace. Los colores viven como custom
// properties para no duplicar estilos; el ember seguía siendo el acento de
// Conecta Moda en el sistema anterior, así que se conserva como hilo de
// continuidad de marca — todo lo demás es una dirección nueva.
//
// Redecidido con Ricardo el 2026-09-12: se abandona a propósito la regla
// anterior de "solo modo claro" — esta vez el oscuro es la identidad, fija
// (no sigue el tema del sistema operativo: es una decisión de marca, igual
// de deliberada que la anterior).
export const palette = {
  paper: "var(--paper)",
  card: "var(--card)",
  cardHover: "var(--card-hover)",
  sand: "var(--sand)",
  ink: "var(--ink)",
  inkSoft: "var(--ink-soft)",
  inkDim: "var(--ink-dim)",
  line: "var(--line)",
  lineSoft: "var(--line-soft)",
  rust: "var(--accent)",
  olive: "var(--pos)",
  mustard: "var(--warn)",
  neg: "var(--neg)",
};

// Fraunces: editorial, con personalidad de revista de moda — evita la
// trampa del display-sans genérico. Plex Mono lee TODO dato (puntajes,
// momentum, códigos): es la voz del instrumento. Plex Sans es la voz de la
// interfaz (botones, nav, cuerpo de texto). Tres registros, tres trabajos.
export const FONT = {
  display: "'Fraunces', Georgia, 'Times New Roman', serif",
  ui: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  mono: "'IBM Plex Mono', ui-monospace, 'SFMono-Regular', monospace",
};

export const THEME_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,340;0,9..144,460;0,9..144,560;0,9..144,650;1,9..144,420;1,9..144,500&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

  .radar {
    --paper: #0B0A09;
    --card: #14120F;
    --card-hover: #1B1815;
    --sand: #1F1A15;
    --ink: #F4EFE6;
    --ink-soft: #9C9488;
    /* El primer valor (#6B6459) daba ~3.38:1 sobre --paper — por debajo del
       4.5:1 de AA para texto normal, el mismo problema que ya se corrigió
       una vez en --ink-soft. Se usa en metadatos, fuentes y códigos, texto
       real que alguien puede querer leer, así que se sube a ~4.6:1. */
    --ink-dim: #80796D;
    --line: #2A2420;
    --line-soft: #201B17;
    --stitch: #3E2F22;
    --accent: #FF5A1F;
    --accent-dim: #4A2210;
    --pos: #3FE07C;
    --pos-bg: rgba(63, 224, 124, 0.13);
    --warn: #FFC24B;
    --warn-bg: rgba(255, 194, 75, 0.13);
    --neg: #FF4F63;
    --neg-bg: rgba(255, 79, 99, 0.13);
    color-scheme: dark;
  }

  .radar { scroll-behavior: smooth; background: var(--paper); }
  .radar * { box-sizing: border-box; }
  .radar [id] { scroll-margin-top: 84px; }
  .radar ::selection { background: var(--accent); color: #0B0A09; }
  .radar :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }

  /* Textura de fondo: un grano finísimo + un leve barrido de líneas
     horizontales, como el fósforo de una pantalla de radar real. Muy sutil
     a propósito — se siente, no se nota. */
  .radar-scanlines {
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image: repeating-linear-gradient(
      to bottom, rgba(244,239,230,0.018) 0px, rgba(244,239,230,0.018) 1px,
      transparent 1px, transparent 3px
    );
    mix-blend-mode: overlay;
  }

  /* El barrido de radar de verdad: un cono girando despacio detrás del
     titular. Es el motivo que le da nombre al panel — no es un adorno
     genérico, es LA metáfora del producto hecha visible. */
  .radar-sweep {
    position: absolute; inset: 0; pointer-events: none; overflow: hidden;
    -webkit-mask-image: radial-gradient(circle at 78% 18%, #000 0%, #000 55%, transparent 78%);
    mask-image: radial-gradient(circle at 78% 18%, #000 0%, #000 55%, transparent 78%);
  }
  .radar-sweep::before {
    content: ""; position: absolute; top: -60%; right: -30%; width: 130%; height: 220%;
    background: conic-gradient(from 0deg at 50% 50%,
      transparent 0deg, transparent 300deg,
      rgba(255,90,31,0.22) 336deg, rgba(255,90,31,0.5) 356deg, transparent 360deg);
    animation: sweep 7s linear infinite;
    transform-origin: 50% 50%;
  }
  .radar-sweep::after {
    content: "";
    position: absolute; top: -60%; right: -30%; width: 130%; height: 220%;
    background-image:
      repeating-radial-gradient(circle at 50% 50%, rgba(244,239,230,0.05) 0, rgba(244,239,230,0.05) 1px, transparent 1px, transparent 72px);
  }
  @keyframes sweep { to { transform: rotate(360deg); } }

  /* Cinta de teletipo: los códigos del radar desfilando como en un tablero
     de salidas o un ticker de mercado. Contenido duplicado una vez para
     que el loop sea perfecto. */
  .ticker {
    overflow: hidden; white-space: nowrap; border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line); background: var(--card);
  }
  .ticker-track {
    display: inline-flex; align-items: center; animation: marquee 46s linear infinite;
    will-change: transform;
  }
  .ticker:hover .ticker-track { animation-play-state: paused; }
  @keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }

  /* Tarjetas: sin sombra — el borde vive adentro, como un panel de
     instrumento remachado a la carcasa. */
  .card-flat {
    background: var(--card);
    box-shadow: inset 0 0 0 1px var(--line);
    border-radius: 3px;
    transition: background-color .15s ease, box-shadow .15s ease;
  }
  .card-flat:hover { background: var(--card-hover); }
  .card-tap { text-align: left; width: 100%; }

  /* Retícula: las cuatro esquinas de una mira de radar, prendidas a
     cualquier tarjeta que reciba la clase .reticle. Se encienden en ember
     al pasar el mouse o cuando la tarjeta está expandida. */
  .reticle { position: relative; }
  .reticle-corner { position: absolute; width: 9px; height: 9px; pointer-events: none; transition: border-color .15s ease; }
  .reticle .corner-tl { top: -1px; left: -1px; border-top: 1.5px solid var(--line-soft); border-left: 1.5px solid var(--line-soft); }
  .reticle .corner-tr { top: -1px; right: -1px; border-top: 1.5px solid var(--line-soft); border-right: 1.5px solid var(--line-soft); }
  .reticle .corner-bl { bottom: -1px; left: -1px; border-bottom: 1.5px solid var(--line-soft); border-left: 1.5px solid var(--line-soft); }
  .reticle .corner-br { bottom: -1px; right: -1px; border-bottom: 1.5px solid var(--line-soft); border-right: 1.5px solid var(--line-soft); }
  .reticle:hover .reticle-corner, .reticle-active .reticle-corner { border-color: var(--accent); }

  .hairline { border-top: 1px solid var(--line); }
  /* Pespunte: divisor punteado que separa lo cualitativo (nombre, decisión)
     de lo cuantitativo (momentum, código) dentro de una misma tarjeta —
     el hilo visible de una costura real, ahora en cobre sobre carbón. */
  .stitch { border-top: 1px dashed var(--stitch); }
  .num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }

  /* Tag de muestra de tela: prendido a la tarjeta como un cartón de color
     físico, con el puntito del hilo — el único elemento que sigue siendo
     literal (es el color real) en un panel que por lo demás es todo señal. */
  .tag {
    position: absolute; top: -10px; left: 18px; width: 30px; height: 30px;
    border-radius: 6px; transform: rotate(-3deg);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.16), 0 3px 10px rgba(0,0,0,.55);
  }
  .tag::after {
    content: ""; position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
    width: 5px; height: 5px; border-radius: 50%; background: var(--card);
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.35);
  }
  .cat-label {
    font-family: ${FONT.mono}; font-size: 10px; letter-spacing: .14em;
    text-transform: uppercase; color: var(--ink-dim); margin: 8px 0 8px;
  }

  /* Chip de contexto neutro (región, etc.) — sigue siendo pastilla, para
     distinguirlo de un dato de instrumento (que va en rectángulo/mono). */
  .chip {
    display: inline-flex; align-items: center; gap: 5px;
    font-family: ${FONT.ui}; font-weight: 600; font-size: 11px; letter-spacing: -0.005em;
    padding: 4px 10px; border-radius: 999px; border: none;
    color: var(--ink-soft); background: var(--sand); white-space: nowrap;
  }
  .chip-dot { width: 5px; height: 5px; border-radius: 999px; flex: none; }

  /* Chip de decisión: ya no es una pastilla rellena — es un LED apagado o
     encendido, como el estado de un contacto en una consola de radar. */
  .led-chip {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: ${FONT.mono}; font-weight: 600; font-size: 10.5px; letter-spacing: .04em;
    text-transform: uppercase; white-space: nowrap;
  }
  .led-dot { width: 6px; height: 6px; border-radius: 999px; flex: none; }

  .navlink {
    font-family: ${FONT.ui}; font-size: 12px; color: var(--ink-soft);
    padding: 4px 0; border-bottom: 1px solid transparent; transition: color .15s, border-color .15s;
  }
  .navlink:hover { color: var(--ink); border-bottom-color: var(--accent); }

  @media (prefers-reduced-motion: reduce) {
    .radar *, .radar *::before, .radar *::after { transition: none !important; animation: none !important; }
  }
`;
