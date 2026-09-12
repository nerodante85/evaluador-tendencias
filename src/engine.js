// Motor de recomendación de compra.
//
// Aquí vive TODA la lógica de puntaje del panel. La UI (Dashboard.jsx) solo
// pinta lo que este archivo decide, y los datos entran desde src/data/.
// Si quieres cambiar cómo se decide una compra — no cómo se ve — este es
// el único archivo que hay que tocar.

import trendsData from "./data/trends.json";
import plan from "./data/plan.json";
import contexto from "./data/contexto.json";
import macro from "./data/macro.json";

export const TRENDS = trendsData.trends;
export const TRENDS_GENERADO = trendsData.generated_at;

export const PRESUPUESTO = plan.presupuesto;
export const MATERIALES = plan.materiales;
export const INSUMOS = plan.insumos;
export const CALENDARIO = plan.calendario;
export const FACTORES = plan.factores;
export const CRITERIOS = plan.criterios;
export const METRICAS = plan.metricas;

export const PINTEREST_PREDICTS = contexto.pinterest;
export const MACRO_CONTEXT = contexto;

// Tasa de cambio: la escribe fetch_macro.py. El algodón es dato de baja
// frecuencia y vive en contexto.json, editado a mano.
export const MACRO = {
  usdcop: {
    actual: macro.usdcop.actual,
    cambio30d: macro.usdcop.cambio_30d_pct,
    direccion: macro.usdcop.direccion,
    trayectoria: macro.usdcop.trayectoria,
    fechaDato: macro.usdcop.fecha_dato,
    fuente: macro.usdcop.fuente,
    live: true,
  },
  algodon: contexto.algodon,
};

// Mapeo manual: qué señales del radar están corroboradas por una tendencia
// independiente de Pinterest Predicts (dos fuentes distintas apuntando al
// mismo lugar = señal más confiable que cualquiera de las dos por separado).
// Se edita en src/data/contexto.json.
export const PINTEREST_CORROBORATION = contexto.pinterestCorroboracion;

export const CATS = [
  { id: "todos", label: "Todos" },
  { id: "color", label: "Colores" },
  { id: "prenda", label: "Prendas" },
  { id: "material", label: "Materiales" },
];

// Con cuatro regiones en el radar, el alcance pasa a ser un filtro de primer
// nivel: no se compra igual una señal de Medellín que una de Tokio.
export const SCOPES = [
  { id: "todos", label: "Todas las regiones" },
  { id: "co", label: "Colombia" },
  { id: "latam", label: "LatAm" },
  { id: "global", label: "Global" },
  { id: "asia", label: "Asia" },
];

export const SCOPE_LABEL = { co: "Colombia", latam: "LatAm", global: "Global", asia: "Asia" };

// geoUsado viene de fetch_trends.py con el código que Google Trends aceptó
// para esa consulta ("" o "global" = búsqueda mundial).
export const GEO_LABEL = {
  CO: "Colombia", global: "Mundial", "": "Mundial", CN: "China", KR: "Corea del Sur",
  JP: "Japón", VE: "Venezuela", US: "EE. UU.", MX: "México", BR: "Brasil",
  PE: "Perú", AR: "Argentina", CL: "Chile",
};
export const geoNombre = (g) => GEO_LABEL[g] ?? g ?? "—";

export const CONF_LABEL = { alta: "Confianza alta", media: "Confianza media", baja: "Confianza baja" };

export const CAT_LABEL = { color: "Colores", prenda: "Prendas", material: "Materiales" };
export const CAT_LABEL_SING = { color: "Color", prenda: "Prenda", material: "Material" };

export const DECISION_RANK = { Comprar: 0, "Probar en lote pequeño": 1, Monitorear: 2, "Evitar / dejar salir": 3 };

export const DECISION_COLOR = {
  Comprar: "var(--pos)",
  "Probar en lote pequeño": "var(--warn)",
  Monitorear: "var(--ink-soft)",
  "Evitar / dejar salir": "var(--neg)",
};

// Fondo pastel para el badge sólido de cada decisión (estilo "Status Badge
// Pill"): el color de arriba pasa a ser el texto, este es el relleno.
export const DECISION_BG = {
  Comprar: "var(--pos-bg)",
  "Probar en lote pequeño": "var(--warn-bg)",
  Monitorear: "var(--line)",
  "Evitar / dejar salir": "var(--neg-bg)",
};

const PUNTOS_CONFIANZA = { alta: 40, media: 20, baja: 5 };

// Combina: confianza del dato + momentum + dirección + búsquedas en
// breakout + corroboración con Pinterest Predicts + si es señal temprana
// de Asia (más exploratoria, menos lista para comprar).
export function computeDecision(t) {
  const reasons = [];
  let score = PUNTOS_CONFIANZA[t.confianza] ?? 5;
  reasons.push(`Confianza ${t.confianza} (+${PUNTOS_CONFIANZA[t.confianza] ?? 5})`);

  const momPts = Math.round(Math.min(30, t.momentum * 0.3));
  score += momPts;
  reasons.push(`Momentum ${t.momentum}/100 (+${momPts})`);

  const dirPts = t.dir === "subiendo" ? 15 : t.dir === "bajando" ? -20 : 0;
  score += dirPts;
  reasons.push(`Dirección ${t.dir} (${dirPts >= 0 ? "+" : ""}${dirPts})`);

  // Las búsquedas marcadas como ruido no cuentan: un pico por un videojuego
  // o un meme no es demanda de moda por más espectacular que se vea el %.
  const utiles = (t.relacionadas || []).filter((r) => !r.ruido);
  // fetch_trends.py solo emite "Breakout" (literal) o "+{value}%" — el
  // "crecimiento" nunca trae otro formato, así que basta comparar contra el
  // literal. Antes también se aceptaba cualquier "+" con 4+ dígitos como
  // señal de breakout aunque pytrends no lo hubiera marcado así; eso podía
  // sumar +15 en vez de +5 a una búsqueda relacionada grande pero no oficial.
  const hasBreakout = utiles.some((r) => r.crecimiento === "Breakout");
  const hasRelated = utiles.length > 0;
  if (hasBreakout) {
    score += 15;
    reasons.push("Búsqueda relacionada en Breakout (+15)");
  } else if (hasRelated) {
    score += 5;
    reasons.push("Búsquedas relacionadas en alza (+5)");
  }

  const corrob = PINTEREST_CORROBORATION[t.id];
  if (corrob) {
    score += 15;
    reasons.push(`Corroborado por Pinterest Predicts: "${corrob}" (+15)`);
  }

  // Distancia de mercado: cuanto más lejos del consumidor colombiano, más
  // traducción hace falta antes de comprar. LatAm comparte clima, cuerpo y
  // canal de proveedores, así que penaliza la mitad que Asia.
  if (t.scope === "asia") {
    score -= 10;
    reasons.push("Señal temprana de Asia — aún no confirmada en mercado local (-10)");
  } else if (t.scope === "latam") {
    score -= 5;
    reasons.push("Señal regional latinoamericana — clima y cuerpo cercanos, pero sin confirmar aquí (-5)");
  }

  score = Math.max(0, Math.min(100, Math.round(score)));

  let label;
  if (t.confianza === "baja") {
    label = "Monitorear";
    reasons.push("Dato insuficiente en Trends → tope en 'Monitorear' sin importar el puntaje");
  } else if (t.dir === "bajando" && !(hasBreakout && corrob)) {
    label = "Evitar / dejar salir";
  } else if (score >= 65) {
    label = "Comprar";
  } else if (score >= 40) {
    label = "Probar en lote pequeño";
  } else {
    label = "Monitorear";
  }

  return { score, label, reasons, hasBreakout, corrob };
}

// Respaldo de una tela = la mejor señal que la sostiene. Se recalcula solo
// cuando entran datos nuevos de Trends.
export function respaldoTela(mat) {
  const señales = mat.senales.map((id) => TRENDS.find((t) => t.id === id)).filter(Boolean);
  if (señales.length === 0) return { label: "Monitorear", score: 0, señales: [] };
  const evaluadas = señales.map((t) => ({ trend: t, dec: computeDecision(t) }));
  const mejor = evaluadas
    .slice()
    .sort((a, b) => DECISION_RANK[a.dec.label] - DECISION_RANK[b.dec.label] || b.dec.score - a.dec.score)[0];
  return { label: mejor.dec.label, score: mejor.dec.score, señales: evaluadas };
}

// --- Autodiagnóstico de una empresa ---
// Marcas lo que hoy ya trabajas y el panel te devuelve: qué tan alineado
// estás con las señales comprables, qué estás dejando sobre la mesa, qué
// tienes en riesgo, y la lista de telas que se desprende de tus señales.
export const PUNTOS_DECISION = { Comprar: 100, "Probar en lote pequeño": 70, Monitorear: 40, "Evitar / dejar salir": 10 };

// --- Señales propias de la empresa ---
// El radar solo mide 30 señales tomadas de prensa y Google Trends. Lo que
// cada empresa vende de verdad casi nunca coincide con esa lista, así que
// aquí se pueden agregar colores, prendas y materiales propios.
//
// Una señal propia no tiene dato de Google Trends todavía, entonces se
// evalúa con evidencia interna (cómo rota en tu tienda, si la ves en el
// mercado, si ya tienes proveedor). Esa lectura es provisional y por diseño
// nunca llega a "Comprar": para eso hay que medirla.
export const EVIDENCIA = {
  rotacion: {
    label: "Cómo rota hoy en tu tienda",
    ayuda: "Lo que ya sabes por ventas propias. Es la evidencia más fuerte que tienes sin Trends.",
    opciones: [
      { id: "alta", label: "Rota bien", pts: 45 },
      { id: "media", label: "Rota normal", pts: 25 },
      { id: "baja", label: "Rota poco", pts: 5 },
      { id: "nueva", label: "Aún no la vendo", pts: 15 },
    ],
  },
  mercado: {
    label: "¿La ves en el mercado local?",
    ayuda: "Si la competencia ya la tiene, hay demanda pero también hay pelea de precio.",
    opciones: [
      { id: "mucha", label: "En todas partes", pts: 20 },
      { id: "algo", label: "Empezando a aparecer", pts: 25 },
      { id: "nada", label: "Nadie la tiene", pts: 10 },
    ],
  },
  proveedor: {
    label: "¿Tienes proveedor resuelto?",
    ayuda: "Una señal sin proveedor confiable no es comprable por buena que sea.",
    opciones: [
      { id: "si", label: "Sí, y con rollo corto", pts: 20 },
      { id: "minimo", label: "Sí, pero con mínimo alto", pts: 10 },
      { id: "no", label: "Todavía no", pts: 0 },
    ],
  },
};

export const ptsDe = (campo, valor) => EVIDENCIA[campo].opciones.find((o) => o.id === valor)?.pts ?? 0;
export const labelDe = (campo, valor) => EVIDENCIA[campo].opciones.find((o) => o.id === valor)?.label ?? "—";

// Evaluación provisional de una señal propia, con la misma escala 0–100 del
// motor principal para que se puedan comparar entre sí.
export function computeDecisionPropia(s) {
  const reasons = [];
  let score = 0;

  ["rotacion", "mercado", "proveedor"].forEach((campo) => {
    const p = ptsDe(campo, s[campo]);
    score += p;
    reasons.push(`${EVIDENCIA[campo].label}: ${labelDe(campo, s[campo])} (+${p})`);
  });

  score = Math.max(0, Math.min(100, score));

  let label;
  if (score >= 55) label = "Probar en lote pequeño";
  else if (score >= 30) label = "Monitorear";
  else label = "Evitar / dejar salir";

  reasons.push("Señal propia sin dato de Google Trends → tope en 'Probar en lote pequeño' hasta medirla");

  return { score, label, reasons, propia: true };
}

export const decisionDe = (t) => (t.propia ? computeDecisionPropia(t) : computeDecision(t));

export function evaluarEmpresa(adoptadas, propias) {
  const universo = [...TRENDS, ...propias];
  const evaluadas = universo.map((t) => ({ t, dec: decisionDe(t), adoptada: adoptadas.includes(t.id) }));

  const mias = evaluadas.filter((e) => e.adoptada);
  const apalancadas = mias.filter((e) => e.dec.label === "Comprar" || e.dec.label === "Probar en lote pequeño");
  const enRiesgo = mias.filter((e) => e.dec.label === "Evitar / dejar salir");
  const oportunidades = evaluadas.filter(
    (e) => !e.adoptada && !e.t.propia && (e.dec.label === "Comprar" || e.dec.label === "Probar en lote pequeño")
  );
  const sinMedir = mias.filter((e) => e.t.propia);

  let puntaje = 0;
  if (mias.length > 0) {
    const base = mias.reduce((acc, e) => acc + PUNTOS_DECISION[e.dec.label], 0) / mias.length;
    const perdidas = evaluadas.filter((e) => !e.t.propia && e.dec.label === "Comprar" && !e.adoptada).length;
    puntaje = Math.max(0, Math.min(100, Math.round(base - Math.min(30, perdidas * 5))));
  }

  const nivel = puntaje >= 70 ? "Fuerte" : puntaje >= 45 ? "Aceptable" : mias.length === 0 ? "Sin evaluar" : "Débil";
  const nivelColor = puntaje >= 70 ? "var(--pos)" : puntaje >= 45 ? "var(--warn)" : "var(--accent)";

  const cobertura = ["color", "prenda", "material"].map((cat) => {
    const total = universo.filter((t) => t.cat === cat).length;
    const propiasCat = mias.filter((e) => e.t.cat === cat).length;
    return { cat, total, propias: propiasCat, pct: total ? Math.round((propiasCat / total) * 100) : 0 };
  });

  const telas = MATERIALES.filter((m) => m.senales.some((id) => adoptadas.includes(id)));
  const telasPropias = mias
    .filter((e) => e.t.propia && e.t.tela)
    .map((e) => ({ tela: e.t.tela, senal: e.t.name, dec: e.dec }));

  return { puntaje, nivel, nivelColor, mias, apalancadas, enRiesgo, oportunidades, sinMedir, cobertura, telas, telasPropias };
}
