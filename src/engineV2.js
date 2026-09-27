// Motor de datos de Radar 2.0. Lee src/data/v2/catalogo.json (lo escribe
// `python -m pipeline.cli exportar`) y lo traduce a lo que necesita
// DashboardV2.jsx. No toca engine.js ni ningún dato de la v1.
import catalogo from "./data/v2/catalogo.json";

export const MERCADOS = catalogo.mercados; // {CO: "Colombia", MX: "México", ES: "España"}
export const TIPOS = catalogo.tipos;
export const METODOLOGIA = catalogo.metodologia;
export const GENERADO = catalogo.generado;
export const HORIZONTE_SCORE = METODOLOGIA?.trend_score?.horizonte_meses ?? 24;

export const TIPO_LABEL = { prenda: "Prendas", corte: "Cortes", tela: "Telas", color: "Colores", estampado: "Estampados", estilo: "Estilos" };
export const TIPO_LABEL_SING = { prenda: "Prenda", corte: "Corte", tela: "Tela", color: "Color", estampado: "Estampado", estilo: "Estilo" };

export const NODOS = Object.entries(catalogo.nodos).map(([id, n]) => ({ id, ...n }));

export const CALIDAD_LABEL = { apta_backtest: "Alto", apta_senal: "Medio" };

export const ESTADO_LABEL = {
  alza_sostenida: "Alza sostenida",
  baja_sostenida: "En baja",
  pico_atencion: "Pico de atención",
  estable: "Estable",
};
export const ESTADO_COLOR = {
  alza_sostenida: "var(--pos)",
  baja_sostenida: "var(--neg)",
  pico_atencion: "var(--warn)",
  estable: "var(--ink-soft)",
};

// Un nodo puede tener datos en varios mercados: para la tarjeta principal
// se usa el mercado con mejor evidencia (score más alto si hay Trend Score;
// si no, el de mayor momentum). El detalle sigue mostrando todos.
export function mejorMercado(nodo) {
  const entradas = Object.entries(nodo.mercados);
  return entradas.sort(([, ma], [, mb]) => {
    if (ma.score_24m != null && mb.score_24m != null) return mb.score_24m - ma.score_24m;
    if (ma.score_24m != null) return -1;
    if (mb.score_24m != null) return 1;
    return (mb.momentum ?? 0) - (ma.momentum ?? 0);
  })[0];
}

// ¿El intervalo de confianza al 95% de esta variable cruza cero? Si cruza,
// el propio Trend Score dice que no hay evidencia sólida de que aporte algo
// (docs/v2/hallazgo-trend-score-fase4.md) — no se puede tratar como parte
// del "por qué" del puntaje aunque el valor crudo de la variable sea real.
// `intervalos` es inyectable (por defecto, los del catálogo real importado
// arriba) solo para que las pruebas puedan fijar un escenario sin depender
// de la calibración vigente del Trend Score, que cambia cada vez que se
// recalibra. El comportamiento por defecto es el de siempre.
function pesoSignificativo(variable, intervalos = METODOLOGIA?.trend_score?.intervalos_95) {
  const ic = intervalos?.[variable];
  if (!ic || ic.length !== 2) return null; // sin dato: ni se afirma ni se niega
  const [lo, hi] = ic;
  return lo > 0 || hi < 0; // true = no cruza cero = sí aporta con la evidencia actual
}

// Evidencia en lenguaje llano — nunca "será", siempre lo que ya se observó.
//
// H-04 de la auditoría del 2026-09-27: antes, esta lista mostraba todas las
// variables por igual, lo que podía leerse como que todas "explican" un
// puntaje alto. Pero el intervalo de confianza de cada variable (calibrado
// en pipeline/trend_score.py, docs/v2/hallazgo-trend-score-fase4.md) puede
// cruzar cero — ahí el modelo real no tiene evidencia sólida de que esa
// variable aporte, aunque el dato crudo sea real. Qué variable cruza cero
// **cambia entre calibraciones** (con la muestra grande del 2026-09-27,
// `saturación` empezó a cruzar cero, cosa que la fase 4 ya anticipaba como
// posible con más datos) — por eso el chequeo es dinámico contra
// `intervalos_95`, no una lista fija de nombres.
function variableConRespaldo(variable, intervalos) {
  const sig = pesoSignificativo(variable, intervalos);
  return sig !== false; // null (sin dato) se trata como "no se sabe" -> no se marca
}

export function evidencia(m, intervalos = METODOLOGIA?.trend_score?.intervalos_95) {
  const puntos = [];
  const sinRespaldo = [];
  const agregar = (variable, texto) => (variableConRespaldo(variable, intervalos) ? puntos : sinRespaldo).push(texto);

  if (m.persistencia != null) {
    if (m.persistencia >= 9) agregar("persistencia", `Se mantuvo por encima de su nivel base ${m.persistencia} de los últimos 12 meses — no es un pico aislado.`);
    else if (m.persistencia <= 3) agregar("persistencia", "Poca persistencia: el nivel actual no se sostuvo la mayoría de los últimos 12 meses.");
  }
  if (m.crecimiento != null) {
    if (m.crecimiento >= 0.25) agregar("crecimiento", "Crecimiento sostenido de búsquedas frente al período anterior.");
    else if (m.crecimiento <= -0.25) agregar("crecimiento", "Caída sostenida de búsquedas frente al período anterior.");
  }
  if (m.aceleracion != null) {
    if (m.aceleracion > 0.15) agregar("aceleracion", "El ritmo de crecimiento se está acelerando frente a hace un año.");
    else if (m.aceleracion < -0.15) agregar("aceleracion", "El ritmo de crecimiento se está frenando frente a hace un año.");
  }
  if (m.volatilidad != null && m.volatilidad > 0.6) {
    agregar("volatilidad", "Lectura poco estable (alta volatilidad): tomar con más cautela de lo habitual.");
  }
  if (m.saturacion != null && m.saturacion >= 0.9) {
    agregar("saturacion", "Está en su nivel más alto de los últimos años — puede tener poco margen adicional de crecimiento.");
  }
  if (m.estacional) {
    // La estacionalidad no entra al Trend Score a propósito (no es mejor ni
    // peor, es un contexto distinto — docs/v2/hallazgo-trend-score-fase4.md),
    // así que no tiene sentido buscarle un intervalo: siempre es contexto.
    puntos.push("El patrón coincide con estacionalidad de calendario: parte de la señal puede ser de temporada, no de tendencia.");
  }

  // Las que no tienen respaldo estadístico van al final, marcadas — son un
  // dato real (así está la serie), pero el Trend Score no las usa para
  // decidir el puntaje de arriba.
  sinRespaldo.forEach((texto) => puntos.push(`${texto} (dato de contexto: el modelo no encontró evidencia sólida de que esto mueva el puntaje)`));

  return puntos;
}

// {modelo, horizonte, ...metricas} a partir de las claves "modelo|horizonte"
// del backtesting, para la página de metodología.
export function filasBacktesting() {
  const metricas = METODOLOGIA?.backtesting?.metricas;
  if (!metricas) return [];
  return Object.entries(metricas).map(([clave, m]) => {
    const [modelo, horizonte] = clave.split("|");
    return { modelo, horizonte: Number(horizonte), ...m };
  });
}

export function claseMayoritariaPorHorizonte() {
  return METODOLOGIA?.backtesting?.clase_mayoritaria ?? {};
}
