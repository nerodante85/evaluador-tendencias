import { useMemo, useState } from "react";
import { Radar, ChevronDown, TrendingUp, TrendingDown, Minus, Zap } from "lucide-react";

import { palette, FONT, THEME_CSS } from "./theme.js";
import {
  MERCADOS,
  TIPOS,
  TIPO_LABEL,
  TIPO_LABEL_SING,
  NODOS,
  CALIDAD_LABEL,
  ESTADO_LABEL,
  ESTADO_COLOR,
  mejorMercado,
  evidencia,
  filasBacktesting,
  claseMayoritariaPorHorizonte,
  HORIZONTE_SCORE,
  GENERADO,
  METODOLOGIA,
} from "./engineV2.js";

// Radar 2.0 reutiliza el lenguaje visual "Radar Terminal" ya aprobado para
// la v1 (mismo theme.js), pero es un componente y un dato completamente
// aparte: no importa nada de engine.js ni de Dashboard.jsx.

function SectionTitle({ eyebrow, title, sub }) {
  return (
    <div className="mb-5">
      <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkDim, fontFamily: FONT.mono }}>{eyebrow}</p>
      <h2 style={{ fontFamily: FONT.display, fontWeight: 460, fontSize: "1.9rem", lineHeight: 1.1, letterSpacing: "-0.01em", color: palette.ink }}>{title}</h2>
      {sub && <p className="text-sm mt-2 leading-relaxed max-w-2xl" style={{ color: palette.inkSoft }}>{sub}</p>}
    </div>
  );
}

function Collapsible({ label, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mt-4">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1.5 text-xs font-medium" style={{ color: palette.ink }}>
        <ChevronDown size={13} style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
        {label}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  );
}

const ESTADO_ICONO = { alza_sostenida: TrendingUp, baja_sostenida: TrendingDown, pico_atencion: Zap, estable: Minus };

// H-09 de la auditoría del 2026-09-27: este chip describe una ventana que ya
// terminó (los últimos 12 meses medidos), no una predicción — antes ese
// aviso vivía solo en el footer del panel. El tooltip lo deja junto al chip
// mismo, donde de verdad se lee.
const ESTADO_TOOLTIP = "Describe los últimos 12 meses medidos, no una predicción de lo que viene. Para eso está el puntaje (score), que sí mira hacia adelante.";

function EstadoChip({ estado }) {
  const color = ESTADO_COLOR[estado] || palette.inkDim;
  const Icono = ESTADO_ICONO[estado] || Minus;
  return (
    <span className="led-chip" title={ESTADO_TOOLTIP}>
      <span className="led-dot" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
      <span style={{ color, display: "inline-flex", alignItems: "center", gap: 4 }}>
        <Icono size={12} />
        {ESTADO_LABEL[estado] || estado}
      </span>
    </span>
  );
}

function nivelScore(score) {
  if (score == null) return null;
  if (score >= 65) return { label: "Alto", color: palette.olive };
  if (score >= 40) return { label: "Medio", color: palette.mustard };
  return { label: "Bajo", color: palette.inkDim };
}

function NodoCard({ nodo, expanded, onToggle }) {
  const [codigoMercado, m] = mejorMercado(nodo);
  const nivel = nivelScore(m.score_24m);
  const puntos = evidencia(m);
  const otrosMercados = Object.entries(nodo.mercados).filter(([c]) => c !== codigoMercado);

  return (
    <button
      onClick={onToggle}
      className={`card-flat card-tap reticle p-5 h-full flex flex-col ${expanded ? "reticle-active" : ""}`}
      style={{ position: "relative", boxShadow: expanded ? "inset 0 0 0 1.5px var(--accent)" : undefined }}
    >
      <span className="reticle-corner corner-tl" />
      <span className="reticle-corner corner-tr" />
      <span className="reticle-corner corner-bl" />
      <span className="reticle-corner corner-br" />

      <p className="cat-label">{TIPO_LABEL_SING[nodo.tipo]}</p>

      <div className="flex items-start justify-between gap-3">
        <p className="leading-tight min-w-0" style={{ color: palette.ink, fontSize: "1.02rem", fontWeight: 600, letterSpacing: "-0.01em", fontFamily: FONT.ui }}>
          {nodo.nombre}
        </p>
        {m.score_24m != null ? (
          <span className="num text-right shrink-0" style={{ fontFamily: FONT.mono, fontWeight: 600, fontSize: "1.6rem", lineHeight: 1, color: nivel.color }}>
            {m.score_24m}
          </span>
        ) : (
          <span className="font-mono text-[10px] uppercase shrink-0" style={{ color: palette.inkDim }}>sin score</span>
        )}
      </div>

      <div className="flex items-center gap-1.5 mt-2 flex-wrap">
        <EstadoChip estado={m.estado_actual} />
        <span className="chip">{MERCADOS[codigoMercado]}</span>
        {m.estacional && <span className="chip" style={{ color: palette.mustard }}>Estacional</span>}
      </div>

      <div className="flex items-end justify-between gap-3 mt-4 pt-3 stitch" style={{ marginTop: "auto" }}>
        <div>
          <p
            className="num text-[11px]"
            style={{ color: palette.inkDim, fontFamily: FONT.mono }}
            title="Nivel promedio de interés en los últimos 12 meses — no es velocidad de cambio. Para eso está 'aceleración' en la Evidencia de abajo."
          >
            Momentum {m.momentum}
          </p>
          {nivel && <p className="text-[11px] mt-1" style={{ color: palette.inkSoft }}>Puntaje {nivel.label.toLowerCase()} · historia de datos: {CALIDAD_LABEL[m.calidad].toLowerCase()}</p>}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 text-left" style={{ borderTop: `1px solid ${palette.line}` }}>
          <p className="text-[11px] leading-relaxed mb-3" style={{ color: palette.inkDim }}>
            <strong style={{ color: palette.ink }}>{ESTADO_LABEL[m.estado_actual] || m.estado_actual}</strong> describe los últimos 12
            meses ya medidos, no una predicción — el puntaje de abajo (si lo tiene) es lo único de esta tarjeta que mira hacia adelante.
          </p>
          {m.score_24m != null && (
            <p className="text-xs leading-relaxed mb-3" style={{ color: palette.ink }}>
              <strong style={{ color: nivel.color }}>{m.score_24m}/100</strong> — probabilidad estimada de tendencia sostenida al alza en los próximos {HORIZONTE_SCORE} meses, calibrada contra patrones históricos comparables. No es una certeza: en pruebas fuera de muestra, el puntaje acierta el {Math.round((METODOLOGIA?.trend_score?.evaluacion?.auc ?? 0.5) * 100)}% de las veces mejor que el azar (ver metodología).
            </p>
          )}
          {puntos.length > 0 && (
            <div className="mb-3">
              <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkDim }}>Evidencia</p>
              <ul className="text-xs space-y-0.5" style={{ color: palette.ink }}>
                {puntos.map((p, i) => (
                  <li key={i} className="flex gap-1.5">
                    <span style={{ color: palette.rust }}>›</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {otrosMercados.length > 0 && (
            <div className="mb-3">
              <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkDim }}>También con datos en</p>
              <div className="flex flex-wrap gap-1.5">
                {otrosMercados.map(([c, om]) => (
                  <span key={c} className="text-xs px-2 py-0.5 rounded-full font-mono" style={{ color: palette.ink, border: `1px solid ${palette.line}` }}>
                    {MERCADOS[c]}: {om.score_24m != null ? `${om.score_24m}/100` : ESTADO_LABEL[om.estado_actual]}
                  </span>
                ))}
              </div>
            </div>
          )}
          {nodo.relaciones.length > 0 && (
            <div>
              <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkDim }}>Categorías relacionadas</p>
              <div className="flex flex-wrap gap-1.5">
                {nodo.relaciones.map((r) => (
                  <span key={r} className="text-xs px-2 py-0.5 rounded-full" style={{ color: palette.inkSoft, border: `1px dashed ${palette.line}` }}>{r}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </button>
  );
}

function Metodologia() {
  const filas = filasBacktesting();
  const mayoria = claseMayoritariaPorHorizonte();
  const horizontes = [...new Set(filas.map((f) => f.horizonte))].sort((a, b) => a - b);
  const modelos = [...new Set(filas.map((f) => f.modelo))];
  const ev = METODOLOGIA?.trend_score?.evaluacion;

  return (
    <div className="mt-14">
      <SectionTitle
        eyebrow="Cómo se calibró esto"
        title="El historial de aciertos, no una promesa"
        sub="Nada de esto se ajustó a mano para que 'se viera bien'. Cada número sale de comparar, contra series reales, lo que un modelo habría dicho en el pasado contra lo que de verdad pasó después."
      />
      <div className="card-flat p-4 mb-4">
        <p className="text-xs leading-relaxed" style={{ color: palette.ink }}>
          Exactitud = qué tan seguido la proyección de ese modelo coincidió con lo que realmente pasó, probado sobre cortes históricos que el modelo nunca vio. "Adivinar siempre la clase más común" es la vara mínima real — no 25% al azar, porque las categorías no están parejas.
        </p>
      </div>
      <div className="overflow-x-auto rounded-md" style={{ border: `1px solid ${palette.line}` }}>
        <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: palette.card }}>
              <th className="text-left px-3 py-2 font-mono uppercase" style={{ color: palette.inkDim, fontSize: 10 }}>Horizonte</th>
              <th className="text-left px-3 py-2 font-mono uppercase" style={{ color: palette.inkDim, fontSize: 10 }}>Adivinar siempre lo más común</th>
              {modelos.map((m) => (
                <th key={m} className="text-left px-3 py-2 font-mono uppercase" style={{ color: palette.inkDim, fontSize: 10 }}>{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {horizontes.map((h) => (
              <tr key={h} style={{ borderTop: `1px solid ${palette.line}` }}>
                <td className="px-3 py-2 font-mono" style={{ color: palette.ink }}>{h} meses</td>
                <td className="px-3 py-2 font-mono" style={{ color: palette.inkSoft }}>{mayoria[String(h)] != null ? Math.round(mayoria[String(h)] * 100) + "%" : "—"}</td>
                {modelos.map((mod) => {
                  const f = filas.find((x) => x.modelo === mod && x.horizonte === h);
                  return (
                    <td key={mod} className="px-3 py-2 font-mono" style={{ color: palette.ink }}>
                      {f ? `${Math.round(f.exactitud * 100)}%` : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {ev && (
        <p className="text-[11px] mt-3 leading-relaxed" style={{ color: palette.inkDim }}>
          El Trend Score en sí se probó por separado, contra series que nunca vio durante el ajuste: acertó {Math.round(ev.exactitud * 100)}% de las veces (contra {Math.round(ev.exactitud_mayoria * 100)}% de la vara mínima), con un AUC de {ev.auc} (0,5 = igual que el azar).
        </p>
      )}
      <p className="text-[11px] mt-2 leading-relaxed" style={{ color: palette.inkDim }}>
        A 24 meses ningún modelo se acerca a la certeza — es la evidencia real, no un defecto de este panel en particular. Detalle completo: <code>docs/v2/hallazgo-backtesting-fase3.md</code> y <code>docs/v2/hallazgo-trend-score-fase4.md</code> en el repositorio.
      </p>
    </div>
  );
}

export default function DashboardV2() {
  const [tipo, setTipo] = useState("todos");
  const [mercado, setMercado] = useState("todos");
  const [expandedId, setExpandedId] = useState(null);

  const visibles = useMemo(() => {
    return NODOS.filter((n) => (tipo === "todos" || n.tipo === tipo) && (mercado === "todos" || n.mercados[mercado]))
      .slice()
      .sort((a, b) => {
        const [, ma] = mejorMercado(a);
        const [, mb] = mejorMercado(b);
        return (mb.score_24m ?? mb.momentum ?? 0) - (ma.score_24m ?? ma.momentum ?? 0);
      });
  }, [tipo, mercado]);

  const conSenalAlta = NODOS.filter((n) => Object.values(n.mercados).some((m) => m.calidad === "apta_backtest")).length;

  return (
    <div className="radar min-h-screen w-full" style={{ background: palette.paper, fontFamily: FONT.ui, color: palette.ink }}>
      <style>{THEME_CSS}</style>
      <div className="radar-scanlines" aria-hidden="true" />

      <div className="sticky top-0 z-20" style={{ background: palette.paper, borderBottom: `1px solid ${palette.line}`, position: "relative" }}>
        <div className="max-w-5xl mx-auto px-6 h-12 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 min-w-0">
            <Radar size={15} style={{ color: palette.rust }} />
            <span className="text-xs font-medium tracking-wide truncate" style={{ color: palette.ink, fontFamily: FONT.mono }}>RADAR 2.0</span>
            <span className="hidden sm:inline text-xs" style={{ color: palette.inkDim }}>· evidencia de tendencia</span>
          </div>
          <nav className="hidden sm:flex items-center gap-5">
            {[["#senales", "Señales"], ["#metodologia", "Metodología"]].map(([href, label]) => (
              <a key={href} href={href} className="navlink">{label}</a>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 pb-20" style={{ position: "relative", zIndex: 1 }}>
        <header className="pt-14 pb-10" style={{ position: "relative" }}>
          <div className="radar-sweep" aria-hidden="true" />
          <div style={{ position: "relative", zIndex: 1 }}>
            <p className="text-[11px] tracking-[0.24em] uppercase mb-5" style={{ color: palette.inkDim, fontFamily: FONT.mono }}>
              Radar de tendencias · versión 2 (en construcción)
            </p>
            <h1 className="leading-[1.02]" style={{ fontFamily: FONT.display, fontWeight: 460, color: palette.ink, fontSize: "clamp(2.6rem, 6.5vw, 4.6rem)", letterSpacing: "-0.01em" }}>
              Por qué está creciendo,<br />
              <span style={{ fontStyle: "italic", fontWeight: 420, color: palette.rust }}>no solo que está creciendo</span>
            </h1>
            <p className="text-base mt-6 max-w-2xl leading-relaxed" style={{ color: palette.inkSoft }}>
              {NODOS.length} categorías de moda (prendas, cortes, telas, colores, estampados, estilos) en Colombia, México y España, cada una con un puntaje calibrado contra datos históricos reales — no una opinión, un patrón medido. {conSenalAlta} tienen suficiente historia para la lectura más confiable; el resto queda marcado con menos evidencia, no se esconde. Para empresarios de la confección y diseñadoras, no solo para un taller.
            </p>
            <p className="text-xs mt-4 max-w-2xl leading-relaxed" style={{ color: palette.inkDim }}>
              Fuente única por ahora: Google Trends. Ver la metodología abajo antes de tomar cualquier decisión de compra con esto — a 24 meses, ningún modelo se acerca a la certeza, y este panel lo dice explícitamente en vez de esconderlo.
            </p>
          </div>
        </header>

        <div id="senales" className="mt-6">
          <SectionTitle
            eyebrow="El radar"
            title="Tendencias, prendas, cortes, telas, colores y estampados"
            sub="Cada tarjeta trae su puntaje (si tiene suficiente historia para calibrarlo) y el estado actual de la señal. Toca una tarjeta para ver la evidencia en detalle."
          />
          <div className="flex gap-2 flex-wrap items-center">
            {[{ id: "todos", label: "Todos" }, ...TIPOS.map((t) => ({ id: t, label: TIPO_LABEL[t] }))].map((c) => (
              <button
                key={c.id}
                onClick={() => setTipo(c.id)}
                className="px-3 py-1.5 rounded-full text-xs font-medium"
                style={{ background: tipo === c.id ? palette.ink : "transparent", color: tipo === c.id ? palette.paper : palette.ink, border: `1px solid ${palette.ink}` }}
              >
                {c.label}
              </button>
            ))}
            <span className="w-px h-4 mx-1" style={{ background: palette.line }} />
            {[{ id: "todos", label: "Todos los mercados" }, ...Object.entries(MERCADOS).map(([c, n]) => ({ id: c, label: n }))].map((c) => (
              <button
                key={c.id}
                onClick={() => setMercado(c.id)}
                className="px-3 py-1.5 rounded-full text-xs"
                style={{ background: "transparent", color: mercado === c.id ? palette.ink : palette.inkSoft, border: `1px solid ${mercado === c.id ? palette.ink : palette.line}` }}
              >
                {c.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
            {visibles.map((n) => (
              <div key={n.id} className={expandedId === n.id ? "sm:col-span-2 lg:col-span-3" : ""}>
                <NodoCard nodo={n} expanded={expandedId === n.id} onToggle={() => setExpandedId(expandedId === n.id ? null : n.id)} />
              </div>
            ))}
          </div>
          {visibles.length === 0 && (
            <p className="text-sm mt-6" style={{ color: palette.inkSoft }}>Sin resultados para ese filtro.</p>
          )}
        </div>

        <div id="metodologia"><Metodologia /></div>

        <footer className="mt-16 pt-6" style={{ borderTop: `1px solid ${palette.line}` }}>
          <div className="flex flex-wrap gap-x-10 gap-y-4 justify-between">
            <div className="max-w-md">
              <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkDim, fontFamily: FONT.mono }}>Cómo leer este panel</p>
              <p className="text-xs leading-relaxed" style={{ color: palette.inkSoft }}>
                El puntaje es una probabilidad estimada, no un hecho. "Alza sostenida" describe lo que ya pasó en los últimos 12 meses, no lo que va a pasar. Ninguna frase de este panel promete certeza — donde el dato no alcanza, dice "sin score" o "sin datos" en vez de inventar un número.
              </p>
            </div>
            <div>
              <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkDim, fontFamily: FONT.mono }}>Actualización</p>
              <ul className="text-xs space-y-1" style={{ color: palette.inkSoft }}>
                <li>Datos generados: {GENERADO}</li>
                <li>Se actualiza con <code>python -m pipeline.cli exportar</code></li>
                <li>No comparte datos ni motor de puntaje con el radar v1</li>
              </ul>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
