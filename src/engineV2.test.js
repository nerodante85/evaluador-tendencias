// Pruebas del motor de datos de Radar 2.0 (src/engineV2.js).
//
// Misma regla que engine.test.js: nada de aserciones sobre el catálogo real
// (src/data/v2/catalogo.json cambia cada vez que se recalibra el Trend
// Score o se corre el backtesting) — todo con objetos sintéticos.
import { describe, expect, it } from "vitest";
import { evidencia, mejorMercado } from "./engineV2.js";

describe("mejorMercado", () => {
  it("con score en más de un mercado, gana el de mayor score", () => {
    const nodo = { mercados: { CO: { score_24m: 40 }, MX: { score_24m: 80 } } };
    const [codigo] = mejorMercado(nodo);
    expect(codigo).toBe("MX");
  });

  it("un mercado con score le gana a uno sin score, sin importar el momentum", () => {
    const nodo = { mercados: { CO: { score_24m: null, momentum: 99 }, MX: { score_24m: 10, momentum: 1 } } };
    const [codigo] = mejorMercado(nodo);
    expect(codigo).toBe("MX");
  });

  it("sin score en ningún mercado, gana el de mayor momentum", () => {
    const nodo = { mercados: { CO: { score_24m: null, momentum: 20 }, MX: { score_24m: null, momentum: 60 } } };
    const [codigo] = mejorMercado(nodo);
    expect(codigo).toBe("MX");
  });
});

describe("evidencia — H-04: separa lo que tiene respaldo estadístico de lo que no", () => {
  // Intervalo que cruza cero -> el propio modelo dice que no hay evidencia
  // sólida de que esa variable aporte al puntaje (docs/v2/hallazgo-trend-score-fase4.md).
  const intervalosConCrecimientoNoSignificativo = {
    crecimiento: [-0.3, 0.15], // cruza cero
    persistencia: [0.2, 0.6], // no cruza cero
  };

  it("persistencia alta siempre aparece como evidencia normal", () => {
    const puntos = evidencia({ persistencia: 10 }, {});
    expect(puntos[0]).toContain("Se mantuvo por encima de su nivel base");
    expect(puntos[0]).not.toContain("dato de contexto");
  });

  it("crecimiento con intervalo que cruza cero se marca como sin respaldo, no se oculta", () => {
    const puntos = evidencia({ crecimiento: 0.3 }, intervalosConCrecimientoNoSignificativo);
    expect(puntos).toHaveLength(1);
    expect(puntos[0]).toContain("Crecimiento sostenido");
    expect(puntos[0]).toContain("dato de contexto: el modelo no encontró evidencia sólida");
  });

  it("crecimiento con intervalo que NO cruza cero aparece como evidencia normal, sin la marca", () => {
    const puntos = evidencia({ crecimiento: 0.3 }, { crecimiento: [0.1, 0.5] });
    expect(puntos[0]).not.toContain("dato de contexto");
  });

  it("el chequeo aplica a CUALQUIER variable, no a una lista fija — saturación se marca igual que crecimiento si su intervalo cruza cero", () => {
    // Caso real: con la muestra grande del 2026-09-27, el intervalo de
    // saturación empezó a cruzar cero (la fase 4 ya lo había anticipado
    // como posible). Antes de esta generalización, solo crecimiento y
    // aceleración se marcaban — esta prueba fija que ya no es una lista
    // fija de nombres, sino cualquier variable con intervalo disponible.
    const puntos = evidencia({ saturacion: 0.95 }, { saturacion: [-0.02, 0.3] });
    expect(puntos[0]).toContain("nivel más alto");
    expect(puntos[0]).toContain("dato de contexto");
  });

  it("sin intervalos disponibles (catálogo viejo, sin recalibrar), no rompe y no marca nada", () => {
    // {} simula un catálogo sin ningún intervalo calibrado — pasar `undefined`
    // en cambio activaría el valor por defecto real (METODOLOGIA del catálogo
    // importado de verdad), que no es lo que esta prueba quiere aislar.
    const puntos = evidencia({ crecimiento: 0.3, persistencia: 10 }, {});
    expect(puntos.every((p) => !p.includes("dato de contexto"))).toBe(true);
  });

  it("estacionalidad y saturación alta siempre se reportan, tengan o no intervalo", () => {
    const puntos = evidencia({ estacional: true, saturacion: 0.95 }, {});
    expect(puntos.some((p) => p.includes("estacionalidad de calendario"))).toBe(true);
    expect(puntos.some((p) => p.includes("nivel más alto"))).toBe(true);
  });

  it("sin ninguna variable notable, no hay evidencia que mostrar", () => {
    expect(evidencia({}, {})).toEqual([]);
  });
});
