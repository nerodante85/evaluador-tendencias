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

// Evidencia en lenguaje llano — nunca "será", siempre lo que ya se observó.
// Ver docs/v2/hallazgo-trend-score-fase4.md: crecimiento/aceleración solas
// no tienen respaldo estadístico fuerte (se correlacionan con persistencia),
// así que se listan como contexto, no como el argumento principal.
export function evidencia(m) {
  const puntos = [];
  if (m.persistencia != null) {
    if (m.persistencia >= 9) puntos.push(`Se mantuvo por encima de su nivel base ${m.persistencia} de los últimos 12 meses — no es un pico aislado.`);
    else if (m.persistencia <= 3) puntos.push("Poca persistencia: el nivel actual no se sostuvo la mayoría de los últimos 12 meses.");
  }
  if (m.crecimiento != null) {
    if (m.crecimiento >= 0.25) puntos.push("Crecimiento sostenido de búsquedas frente al período anterior.");
    else if (m.crecimiento <= -0.25) puntos.push("Caída sostenida de búsquedas frente al período anterior.");
  }
  if (m.aceleracion != null) {
    if (m.aceleracion > 0.15) puntos.push("El ritmo de crecimiento se está acelerando frente a hace un año.");
    else if (m.aceleracion < -0.15) puntos.push("El ritmo de crecimiento se está frenando frente a hace un año.");
  }
  if (m.volatilidad != null && m.volatilidad > 0.6) {
    puntos.push("Lectura poco estable (alta volatilidad): tomar con más cautela de lo habitual.");
  }
  if (m.saturacion != null && m.saturacion >= 0.9) {
    puntos.push("Está en su nivel más alto de los últimos años — puede tener poco margen adicional de crecimiento.");
  }
  if (m.estacional) {
    puntos.push("El patrón coincide con estacionalidad de calendario: parte de la señal puede ser de temporada, no de tendencia.");
  }
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
