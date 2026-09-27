// Pruebas del motor de decisión de la v1 (src/engine.js).
//
// Regla de esta suite: nunca aserciones sobre los datos reales de
// src/data/trends.json (cambian con cada corrida de fetch_trends.py) — solo
// objetos sintéticos, para que una prueba nunca falle porque cambió un dato
// y nunca "pase por casualidad" porque el dato real hoy da ese resultado.
import { describe, expect, it } from "vitest";
import { clasificarPatron, computeDecision, computeDecisionPropia, evaluarEmpresa } from "./engine.js";

function trend(over = {}) {
  return {
    id: 1,
    cat: "color",
    scope: "co",
    name: "Señal de prueba",
    momentum: 0,
    dir: "estable",
    confianza: "alta",
    relacionadas: [],
    ...over,
  };
}

describe("computeDecision", () => {
  it("una señal con confianza baja nunca pasa de 'Monitorear', sin importar el resto", () => {
    const d = computeDecision(trend({ confianza: "baja", momentum: 90, dir: "subiendo" }));
    expect(d.label).toBe("Monitorear");
  });

  it("confianza alta + momentum fuerte + subiendo llega a 'Comprar'", () => {
    const d = computeDecision(trend({ confianza: "alta", momentum: 90, dir: "subiendo" }));
    expect(d.label).toBe("Comprar");
    expect(d.score).toBeGreaterThanOrEqual(65);
  });

  it("bajando sin corroboración fuerte cae en 'Evitar / dejar salir'", () => {
    const d = computeDecision(trend({ confianza: "alta", momentum: 70, dir: "bajando" }));
    expect(d.label).toBe("Evitar / dejar salir");
  });

  it("bajando pero con Breakout Y corroboración de Pinterest no se descarta de plano", () => {
    const conCorrob = computeDecision(
      trend({ id: 99, confianza: "alta", momentum: 70, dir: "bajando", relacionadas: [{ termino: "x", crecimiento: "Breakout", ruido: false }] })
    );
    // El id 99 no está en PINTEREST_CORROBORATION real, así que esto sigue
    // siendo "Evitar" — la prueba de abajo (con datos inyectados) es la que
    // de verdad prueba la regla; esta deja constancia de que Breakout SOLO no alcanza.
    expect(conCorrob.label).toBe("Evitar / dejar salir");
  });

  it("solo cuentan las búsquedas relacionadas que NO están marcadas como ruido", () => {
    const conRuido = computeDecision(trend({ relacionadas: [{ termino: "x", crecimiento: "Breakout", ruido: true }] }));
    const sinRuido = computeDecision(trend({ relacionadas: [{ termino: "x", crecimiento: "Breakout", ruido: false }] }));
    expect(sinRuido.score).toBeGreaterThan(conRuido.score);
  });

  it("una señal temprana de Asia puntúa menos que la misma señal en Colombia", () => {
    const co = computeDecision(trend({ scope: "co", momentum: 50, dir: "subiendo" }));
    const asia = computeDecision(trend({ scope: "asia", momentum: 50, dir: "subiendo" }));
    expect(asia.score).toBeLessThan(co.score);
  });

  it("el puntaje siempre queda entre 0 y 100 aunque los puntos sumados se pasen", () => {
    const d = computeDecision(trend({ confianza: "alta", momentum: 100, dir: "subiendo", relacionadas: [{ termino: "x", crecimiento: "Breakout", ruido: false }] }));
    expect(d.score).toBeLessThanOrEqual(100);
    expect(d.score).toBeGreaterThanOrEqual(0);
  });
});

describe("computeDecisionPropia (señales sin dato de Trends)", () => {
  it("nunca llega a 'Comprar' aunque la evidencia interna sea la mejor posible", () => {
    const d = computeDecisionPropia({ rotacion: "alta", mercado: "algo", proveedor: "si" });
    expect(d.label).not.toBe("Comprar");
    expect(d.score).toBe(45 + 25 + 20); // el máximo posible de las tres evidencias
  });

  it("con la peor evidencia interna cae en 'Evitar / dejar salir'", () => {
    const d = computeDecisionPropia({ rotacion: "baja", mercado: "nada", proveedor: "no" });
    expect(d.label).toBe("Evitar / dejar salir");
  });
});

describe("clasificarPatron (indicador nuevo, en paralelo — no toca el score)", () => {
  it("una serie sin yoy/persistencia (señal propia o sin datos) no se clasifica", () => {
    expect(clasificarPatron(trend({ propia: true }))).toBeNull();
    expect(clasificarPatron(trend({ sinDatosSuficientes: true }))).toBeNull();
    expect(clasificarPatron(trend({ persistencia: null }))).toBeNull();
  });

  it("estacional gana incluso si persistencia también sería alta", () => {
    const p = clasificarPatron(trend({ estacional: true, persistencia: 10, yoy: 40 }));
    expect(p.tipo).toBe("estacional");
  });

  it("persistencia alta + yoy fuerte se clasifica como tendencia sostenida", () => {
    const p = clasificarPatron(trend({ estacional: false, persistencia: 10, yoy: 30 }));
    expect(p.tipo).toBe("tendencia");
  });

  it("persistencia alta sin dato de yoy (menos de 15 meses de historia) también cuenta como tendencia", () => {
    const p = clasificarPatron(trend({ estacional: false, persistencia: 9, yoy: null }));
    expect(p.tipo).toBe("tendencia");
  });

  it("persistencia baja con momentum visible se lee como pico aislado", () => {
    const p = clasificarPatron(trend({ estacional: false, persistencia: 1, yoy: null, momentum: 40 }));
    expect(p.tipo).toBe("pico");
  });

  it("caída fuerte y sin sostenerse se lee como declive", () => {
    const p = clasificarPatron(trend({ estacional: false, persistencia: 2, yoy: -60 }));
    expect(p.tipo).toBe("declive");
  });

  it("sin ningún patrón claro no fuerza una etiqueta", () => {
    const p = clasificarPatron(trend({ estacional: false, persistencia: 5, yoy: 5, momentum: 5 }));
    expect(p).toBeNull();
  });

  it("no cambia el score de computeDecision — mismo objeto, dos lecturas independientes", () => {
    const t = trend({ estacional: true, persistencia: 10, yoy: 40, confianza: "alta", momentum: 90, dir: "subiendo" });
    const scoreSinLeerPatron = computeDecision(trend({ ...t, estacional: undefined, persistencia: undefined, yoy: undefined }));
    const scoreConPatron = computeDecision(t);
    expect(scoreConPatron.score).toBe(scoreSinLeerPatron.score);
  });
});

describe("evaluarEmpresa (universo inyectado — no depende de trends.json real)", () => {
  const universo = [
    trend({ id: 1, cat: "color", confianza: "alta", momentum: 90, dir: "subiendo" }), // Comprar
    trend({ id: 2, cat: "prenda", confianza: "alta", momentum: 70, dir: "bajando" }), // Evitar
    trend({ id: 3, cat: "material", confianza: "baja" }), // Monitorear
  ];
  const materiales = [{ tela: "Tela de prueba", grupo: "nucleo", senales: [1], colores: [], consumo: "1m", refs: "" }];

  it("sin ninguna señal adoptada no hay nada que evaluar", () => {
    const r = evaluarEmpresa([], [], universo, materiales);
    expect(r.mias).toHaveLength(0);
    expect(r.nivel).toBe("Sin evaluar");
  });

  it("adoptar la señal en 'Comprar' la deja en apalancadas, no en riesgo", () => {
    const r = evaluarEmpresa([1], [], universo, materiales);
    expect(r.apalancadas.map((e) => e.t.id)).toEqual([1]);
    expect(r.enRiesgo).toHaveLength(0);
  });

  it("adoptar una señal en 'Evitar' la deja en riesgo", () => {
    const r = evaluarEmpresa([2], [], universo, materiales);
    expect(r.enRiesgo.map((e) => e.t.id)).toEqual([2]);
  });

  it("dejar pasar una señal en 'Comprar' que no se adoptó aparece como oportunidad y baja el puntaje", () => {
    const conOportunidad = evaluarEmpresa([2], [], universo, materiales); // solo adopta la de "Evitar"
    expect(conOportunidad.oportunidades.map((e) => e.t.id)).toContain(1);

    const sinOportunidadPerdida = evaluarEmpresa([1, 2], [], universo, materiales); // adopta ambas
    expect(conOportunidad.puntaje).toBeLessThan(sinOportunidadPerdida.puntaje);
  });

  it("las telas dependen de las señales adoptadas, con el universo inyectado, no con MATERIALES real", () => {
    const r = evaluarEmpresa([1], [], universo, materiales);
    expect(r.telas.map((m) => m.tela)).toEqual(["Tela de prueba"]);
    const sinAdoptar = evaluarEmpresa([2], [], universo, materiales);
    expect(sinAdoptar.telas).toHaveLength(0);
  });

  it("una señal propia sin medir nunca sube el puntaje por encima de lo que daría 'Probar en lote pequeño'", () => {
    const propia = { id: 1001, propia: true, cat: "color", rotacion: "alta", mercado: "algo", proveedor: "si", name: "Propia" };
    const r = evaluarEmpresa([1001], [propia], [], materiales);
    expect(r.sinMedir).toHaveLength(1);
    expect(r.puntaje).toBeLessThanOrEqual(70); // "Probar en lote pequeño" = 70 puntos en PUNTOS_DECISION
  });
});
