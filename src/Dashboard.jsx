import { useState } from "react";
import { TrendingUp, TrendingDown, Minus, Pin, ChevronDown, Pencil, Check, Plus, X } from "lucide-react";

import { palette, FONT, THEME_CSS } from "./theme.js";
import {
  TRENDS,
  MACRO,
  MACRO_CONTEXT,
  PINTEREST_PREDICTS,
  PRESUPUESTO,
  MATERIALES,
  INSUMOS,
  CALENDARIO,
  FACTORES,
  CRITERIOS,
  METRICAS,
  CATS,
  SCOPES,
  SCOPE_LABEL,
  CONF_LABEL,
  CAT_LABEL,
  CAT_LABEL_SING,
  DECISION_RANK,
  DECISION_COLOR,
  DECISION_BG,
  EVIDENCIA,
  computeDecision,
  respaldoTela,
  evaluarEmpresa,
  geoNombre,
  labelDe,
} from "./engine.js";

const CONF_COLOR = { alta: palette.inkSoft, media: palette.inkSoft, baja: palette.inkSoft };

const dirIcon = (dir) => {
  if (dir === "subiendo") return <TrendingUp size={14} />;
  if (dir === "bajando") return <TrendingDown size={14} />;
  return <Minus size={14} />;
};
// Subir o bajar no es bueno ni malo: es dirección. Solo el alza recibe el
// acento; lo demás queda neutro para que el color signifique una sola cosa
// en todo el panel — la decisión de compra.
const dirColor = (dir) => (dir === "subiendo" ? palette.rust : palette.inkSoft);

// Sparkline con relleno tenue y punto final marcado: el último valor es el
// que importa para decidir, así que se señala en vez de dejarlo al ojo.
function Sparkline({ points, color, w = 76, h = 26 }) {
  const max = Math.max(...points), min = Math.min(...points);
  const range = max - min || 1;
  const pts = points.map((p, i) => [(i / (points.length - 1)) * w, h - ((p - min) / range) * (h - 4) - 2]);
  const linea = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${linea} ${w},${h} 0,${h}`;
  const [fx, fy] = pts[pts.length - 1];
  return (
    <svg width={w} height={h} className="shrink-0" aria-hidden="true">
      <polygon points={area} fill={color} opacity="0.08" />
      <polyline points={linea} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={fx} cy={fy} r="2.2" fill={color} />
    </svg>
  );
}

// Etiqueta de decisión: punto de color + texto. Un bloque relleno grita;
// esto se lee igual de rápido y deja que los swatches sean lo único
// saturado de la pantalla.
function DecisionChip({ label, score }) {
  return (
    <span className="chip" style={{ color: DECISION_COLOR[label], background: DECISION_BG[label] }}>
      {label}
      {score !== undefined && <span className="num" style={{ opacity: 0.75 }}>{score}</span>}
    </span>
  );
}

function SectionTitle({ eyebrow, title, sub }) {
  return (
    <div className="mb-5">
      <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>{eyebrow}</p>
      <h2 style={{ fontFamily: FONT.display, fontWeight: 400, fontSize: "1.9rem", lineHeight: 1.1, letterSpacing: "-0.01em", color: palette.ink }}>{title}</h2>
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

function DecisionLegend() {
  const rows = [
    { label: "Comprar", color: DECISION_COLOR.Comprar, desc: "Confianza alta/media + momentum fuerte + no está bajando (o baja pero con breakout corroborado por Pinterest)." },
    { label: "Probar en lote pequeño", color: DECISION_COLOR["Probar en lote pequeño"], desc: "Señal real pero no lo bastante fuerte para apostar en volumen. Pide MOQ chico y mide sell-through antes de reordenar." },
    { label: "Monitorear", color: DECISION_COLOR.Monitorear, desc: "Dato insuficiente en Trends (confianza baja) o puntaje bajo. No hay base para comprar todavía, pero vale la pena seguir viéndola." },
    { label: "Evitar / dejar salir", color: DECISION_COLOR["Evitar / dejar salir"], desc: "Tendencia bajando sin corroboración fuerte. Si ya tienes inventario, es momento de liquidar, no de reponer." },
  ];
  return (
    <Collapsible label="¿Cómo se calcula la recomendación de compra?">
      <div className="card-flat p-4">
        <p className="text-xs leading-relaxed mb-2" style={{ color: palette.ink }}>
          Cada señal suma o resta puntos (0–100): confianza del dato (+5 a +40), momentum (hasta +30), dirección
          (+15 subiendo / −20 bajando), búsqueda relacionada en Breakout (+15), corroboración independiente con
          Pinterest Predicts (+15), y una penalización si es señal temprana de Asia aún no confirmada localmente (−10).
          Toca cualquier tarjeta para ver el desglose exacto de esa señal.
        </p>
        <div className="space-y-1.5">
          {rows.map((r) => (
            <div key={r.label} className="flex items-start gap-2">
              <span className="font-mono text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0" style={{ color: r.color, background: DECISION_BG[r.label] }}>
                {r.label}
              </span>
              <p className="text-xs" style={{ color: palette.inkSoft }}>{r.desc}</p>
            </div>
          ))}
        </div>
        <p className="text-[10px] mt-2" style={{ color: palette.inkSoft }}>
          Esto no reemplaza tu criterio ni el sell-through real de tu tienda (todavía no conectado) — es una forma de ordenar señales dispersas, no una garantía.
        </p>
      </div>
    </Collapsible>
  );
}

function SwatchCard({ trend, expanded, onToggle }) {
  const decision = computeDecision(trend);
  return (
    <button
      onClick={onToggle}
      className="card-flat card-tap p-5 h-full flex flex-col"
      style={{ position: "relative", boxShadow: expanded ? "inset 0 0 0 1.5px var(--ink)" : undefined }}
    >
      {/* Tag de muestra de tela prendido a la tarjeta, como un cartón de
          color físico — incluso las señales sin color llevan un tag neutro
          para mantener el ritmo visual del muestrario. */}
      <span className="tag" style={{ background: trend.swatch || "var(--line)" }} />
      <p className="cat-label">{CAT_LABEL_SING[trend.cat]}</p>

      <div className="flex items-start justify-between gap-3">
        <p
          className="leading-tight min-w-0"
          style={{ color: palette.ink, fontSize: "1.02rem", fontWeight: 600, letterSpacing: "-0.01em" }}
        >
          {trend.name}
        </p>
        <span className="num text-right shrink-0" style={{ fontFamily: FONT.display, fontSize: "1.75rem", lineHeight: 1, color: palette.ink }}>
          {decision.score}
        </span>
      </div>

      <div className="flex items-center gap-1.5 mt-2 flex-wrap">
        <DecisionChip label={decision.label} />
        <span className="chip">{SCOPE_LABEL[trend.scope]}</span>
      </div>

      <div className="flex items-end justify-between gap-3 mt-4 pt-3 stitch" style={{ marginTop: "auto" }}>
        <div>
          <div className="flex items-center gap-1 text-xs" style={{ color: dirColor(trend.dir) }}>
            {dirIcon(trend.dir)}
            <span className="capitalize">{trend.dir}</span>
          </div>
          <p className="num text-[11px] mt-1" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
            Momentum {trend.momentum}
          </p>
        </div>
        <Sparkline points={trend.traj} color={dirColor(trend.dir)} />
      </div>

      <div className="mt-3 h-px" style={{ background: palette.lineSoft }}>
        <div className="h-px" style={{ width: `${trend.momentum}%`, background: dirColor(trend.dir) }} />
      </div>

      <div className="flex items-center justify-between mt-2.5">
        <span className="text-[10px] tracking-widest uppercase" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>{trend.code}</span>
        {trend.confianza && (
          <span className="flex items-center gap-1 text-[10px]" style={{ color: CONF_COLOR[trend.confianza], fontFamily: FONT.mono }}>
            <span className="chip-dot" style={{ background: "currentColor" }} />
            {CONF_LABEL[trend.confianza]}
          </span>
        )}
      </div>

      {expanded && (
        <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${palette.line}` }}>
          <div className="mb-3">
            <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>
              Por qué "{decision.label}"
            </p>
            <ul className="text-xs space-y-0.5" style={{ color: palette.ink }}>
              {decision.reasons.map((r, i) => (
                <li key={i} className="flex gap-1.5">
                  <span style={{ color: palette.inkSoft }}>·</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-sm leading-relaxed" style={{ color: palette.ink }}>
            {trend.note}
          </p>

          {MATERIALES.some((m) => m.senales.includes(trend.id)) && (
            <div className="mt-2">
              <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>
                Telas que dependen de esta señal
              </p>
              <div className="flex flex-wrap gap-1.5">
                {MATERIALES.filter((m) => m.senales.includes(trend.id)).map((m, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded-full" style={{ color: palette.ink, border: `1px solid ${palette.line}` }}>
                    {m.tela}
                  </span>
                ))}
              </div>
            </div>
          )}

          {trend.relacionadas && trend.relacionadas.length > 0 && (
            <div className="mt-2">
              <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>
                Búsquedas relacionadas en alza
              </p>
              <div className="flex flex-wrap gap-1.5">
                {trend.relacionadas.map((r, i) => (
                  <span
                    key={i}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      background: !r.ruido && r.crecimiento === "Breakout" ? palette.rust : "transparent",
                      color: r.ruido ? palette.inkSoft : r.crecimiento === "Breakout" ? palette.card : palette.ink,
                      border: `1px ${r.ruido ? "dashed" : "solid"} ${!r.ruido && r.crecimiento === "Breakout" ? palette.rust : palette.line}`,
                      opacity: r.ruido ? 0.65 : 1,
                    }}
                  >
                    {r.termino} <span style={{ opacity: 0.8 }}>({r.crecimiento})</span>
                    {r.ruido && <span className="font-mono text-[9px] ml-1" style={{ color: palette.mustard }}>ruido</span>}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span
              className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase"
              style={{
                color: trend.sinDatosSuficientes ? palette.mustard : palette.olive,
                border: `1px solid ${trend.sinDatosSuficientes ? palette.mustard : palette.olive}`,
              }}
            >
              {trend.sinDatosSuficientes ? "Sin volumen en Trends" : `Google Trends · ${geoNombre(trend.geoUsado)}`}
            </span>
            <p className="font-mono text-[10px] uppercase tracking-wide" style={{ color: palette.inkSoft }}>
              Fuente: {trend.source}
            </p>
          </div>
        </div>
      )}
    </button>
  );
}

function PlanMateriales() {
  const [grupo, setGrupo] = useState("todos");
  const [openTela, setOpenTela] = useState(null);
  const lista = MATERIALES.filter((m) => grupo === "todos" || m.grupo === grupo);

  return (
    <div className="mt-10">
      <SectionTitle
        eyebrow="Plan de compra"
        title="Qué telas comprar, y por qué"
        sub="Cada tela está amarrada a las señales del radar que la justifican: el respaldo se recalcula solo cuando entran datos nuevos de Google Trends. Los consumos son estimados para talla M en tela de 1,50 m de ancho, sin casar estampado — ajústalos con tu trazo real."
      />

      {/* Reparto de presupuesto */}
      <div className="card-flat p-4 mb-4">
        <p className="font-mono text-[10px] uppercase tracking-wide mb-2" style={{ color: palette.inkSoft }}>
          Reparto sugerido del presupuesto de telas
        </p>
        <div className="flex h-2.5 rounded-full overflow-hidden mb-2">
          {PRESUPUESTO.map((p) => (
            <div key={p.id} style={{ width: `${p.pct}%`, background: p.color }} />
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {PRESUPUESTO.map((p) => (
            <div key={p.id}>
              <p className="text-xs font-semibold" style={{ color: p.color }}>{p.pct}% {p.label}</p>
              <p className="text-[11px] leading-snug" style={{ color: palette.inkSoft }}>{p.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Filtro por grupo */}
      <div className="flex gap-2 flex-wrap mb-3">
        {[{ id: "todos", label: "Todas las telas", color: palette.ink }, ...PRESUPUESTO.map((p) => ({ id: p.id, label: p.label, color: p.color }))].map((g) => (
          <button
            key={g.id}
            onClick={() => setGrupo(g.id)}
            className="px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: grupo === g.id ? g.color : "transparent",
              color: grupo === g.id ? palette.paper : g.color,
              border: `1px solid ${g.color}`,
            }}
          >
            {g.label}
          </button>
        ))}
      </div>

      <div className="rounded-md overflow-hidden" style={{ border: `1px solid ${palette.line}` }}>
        {lista.map((m, i) => {
          const resp = respaldoTela(m);
          const grp = PRESUPUESTO.find((p) => p.id === m.grupo);
          const isOpen = openTela === m.tela;
          return (
            <div key={i} style={{ borderBottom: i < lista.length - 1 ? `1px solid ${palette.line}` : "none" }}>
              <button
                onClick={() => setOpenTela(isOpen ? null : m.tela)}
                className="w-full text-left px-4 py-3"
                style={{ background: palette.card, borderLeft: `3px solid ${grp.color}` }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase" style={{ color: grp.color, border: `1px solid ${grp.color}` }}>
                        {grp.label}
                      </span>
                      <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase" style={{ color: DECISION_COLOR[resp.label], background: DECISION_BG[resp.label] }}>
                        {resp.label}
                      </span>
                    </div>
                    <p className="text-sm font-semibold mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui }}>
                      {m.tela}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: palette.inkSoft }}>{m.refs}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-mono text-sm" style={{ color: palette.ink }}>{m.consumo}</p>
                    <p className="text-[10px]" style={{ color: palette.inkSoft }}>por prenda</p>
                    <ChevronDown size={14} className="ml-auto mt-1" style={{ color: palette.inkSoft, transform: isOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
                  </div>
                </div>
              </button>

              {isOpen && (
                <div className="px-4 py-3" style={{ background: palette.paper }}>
                  <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>Colores a comprar</p>
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {m.colores.map((c, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 rounded-full" style={{ color: palette.ink, border: `1px solid ${palette.line}` }}>{c}</span>
                    ))}
                  </div>
                  <p className="font-mono text-[9px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>Señales del radar que la sostienen</p>
                  <div className="space-y-1">
                    {resp.señales.map(({ trend, dec }) => (
                      <div key={trend.id} className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm shrink-0" style={{ color: DECISION_COLOR[dec.label], background: DECISION_BG[dec.label] }}>
                          {dec.score}
                        </span>
                        <span className="text-xs" style={{ color: palette.ink }}>{trend.name}</span>
                        <span className="text-[10px]" style={{ color: palette.inkSoft }}>· {dec.label} · confianza {trend.confianza}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] mt-2 leading-relaxed" style={{ color: palette.inkSoft }}>
                    El respaldo de la tela toma la mejor de sus señales. Si todas están en "Monitorear", la tela sigue
                    siendo válida como núcleo, pero no hay dato que justifique subir el volumen de compra.
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <Collapsible label={`Insumos y accesorios (${INSUMOS.length} grupos) — comprar en paralelo a la tela, no después`}>
        <div className="rounded-md overflow-hidden" style={{ border: `1px solid ${palette.line}` }}>
          {INSUMOS.map((it, i) => (
            <div key={i} className="px-4 py-2.5" style={{ background: palette.card, borderBottom: i < INSUMOS.length - 1 ? `1px solid ${palette.line}` : "none" }}>
              <p className="text-xs font-semibold" style={{ color: palette.ink }}>{it.grupo}</p>
              <p className="text-xs mt-0.5" style={{ color: palette.ink }}>{it.que}</p>
              <p className="text-[11px] mt-0.5" style={{ color: palette.inkSoft }}>{it.criterio}</p>
            </div>
          ))}
        </div>
      </Collapsible>
    </div>
  );
}

function CriteriosYCalendario() {
  return (
    <div className="mt-10">
      <SectionTitle
        eyebrow="Antes de la orden de compra"
        title="Lo que la tendencia no te dice"
        sub="El radar dice qué está subiendo. Estos seis factores deciden si esa señal se convierte en metros de tela."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {FACTORES.map((f, i) => (
          <div key={i} className="card-flat p-4">
            <p className="font-mono text-[9px] uppercase tracking-widest" style={{ color: palette.rust }}>{f.n}</p>
            <p className="text-sm font-semibold mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui }}>{f.titulo}</p>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{f.texto}</p>
          </div>
        ))}
      </div>

      <Collapsible label="Filtro de 5 preguntas por señal (si falla dos, no se compra)">
        <div className="card-flat p-4">
          <ol className="space-y-2.5">
            {CRITERIOS.map((c, i) => (
              <li key={i} className="flex gap-2.5">
                <span className="font-mono text-[10px] shrink-0 pt-0.5" style={{ color: palette.rust }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="text-xs font-semibold" style={{ color: palette.ink }}>{c.p}</p>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: palette.inkSoft }}>{c.d}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </Collapsible>

      <div className="mt-8">
        <SectionTitle
          eyebrow="Ritmo de compra"
          title="Calendario 12 meses"
          sub="Secuencia para taller propio con dos entregas al año."
        />
        <div className="rounded-md overflow-hidden" style={{ border: `1px solid ${palette.line}` }}>
          {CALENDARIO.map((c, i) => (
            <div key={i} className="px-4 py-3" style={{ background: palette.card, borderBottom: i < CALENDARIO.length - 1 ? `1px solid ${palette.line}` : "none" }}>
              <p className="font-mono text-[10px] uppercase tracking-wide" style={{ color: palette.rust }}>{c.ventana}</p>
              <p className="text-xs mt-1" style={{ color: palette.ink }}>{c.hacer}</p>
              <p className="text-xs mt-0.5" style={{ color: palette.inkSoft }}>
                <span style={{ fontWeight: 600 }}>Comprar:</span> {c.comprar}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8">
        <SectionTitle
          eyebrow="Cierre del ciclo"
          title="Qué medir para que la próxima compra sea mejor"
          sub="Estos cuatro números son los que deberían alimentar el radar del año siguiente."
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {METRICAS.map((m, i) => (
            <div key={i} className="rounded-sm p-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `3px solid ${palette.olive}` }}>
              <p className="text-sm font-semibold" style={{ color: palette.ink, fontFamily: FONT.ui }}>{m.m}</p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{m.d}</p>
            </div>
          ))}
        </div>
        <p className="text-[11px] mt-3 leading-relaxed" style={{ color: palette.inkSoft }}>
          Siguiente paso sugerido: registrar por señal si se compró y qué sell-through obtuvo. En dos temporadas el
          panel te dice cuáles fuentes aciertan para este mercado, y la decisión deja de ser intuición.
        </p>
      </div>
    </div>
  );
}

function ListaSenales({ titulo, color, items, vacio }) {
  return (
    <div className="rounded-sm p-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `3px solid ${color}` }}>
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-xs font-semibold" style={{ color: palette.ink }}>{titulo}</p>
        <span className="font-mono text-xs" style={{ color }}>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="text-[11px]" style={{ color: palette.inkSoft }}>{vacio}</p>
      ) : (
        <ul className="space-y-1">
          {items.map(({ t, dec }) => (
            <li key={t.id} className="flex items-start gap-1.5">
              <span className="font-mono text-[9px] px-1 py-0.5 rounded-sm shrink-0 mt-0.5" style={{ color: DECISION_COLOR[dec.label], background: DECISION_BG[dec.label] }}>
                {dec.score}
              </span>
              <span className="text-xs leading-snug" style={{ color: palette.ink }}>
                {t.name}
                {t.propia && <span className="font-mono text-[9px] ml-1" style={{ color: palette.mustard }}>· propia</span>}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const SENAL_VACIA = { name: "", cat: "color", swatch: "#8A8570", query: "", tela: "", rotacion: "media", mercado: "algo", proveedor: "si" };

function FormularioSenal({ onAgregar, onCancelar }) {
  const [f, setF] = useState(SENAL_VACIA);
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  const valido = f.name.trim().length > 1;

  return (
    <div className="rounded-sm p-3 mb-3" style={{ background: palette.card, border: `1px solid ${palette.rust}` }}>
      <p className="font-mono text-[10px] uppercase tracking-wide mb-2" style={{ color: palette.rust }}>
        Nueva señal de tu empresa
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-[11px] block mb-1" style={{ color: palette.inkSoft }}>Nombre</label>
          <input
            autoFocus
            value={f.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="Ej. Azul rey, chaleco acolchado, chalis"
            className="w-full text-sm px-2 py-1.5 rounded-sm outline-none"
            style={{ background: palette.paper, color: palette.ink, border: `1px solid ${palette.line}` }}
          />
        </div>

        <div>
          <label className="text-[11px] block mb-1" style={{ color: palette.inkSoft }}>Categoría</label>
          <div className="flex gap-1.5">
            {["color", "prenda", "material"].map((c) => (
              <button
                key={c}
                onClick={() => set("cat", c)}
                className="px-2.5 py-1.5 rounded-full text-xs font-medium flex-1"
                style={{
                  background: f.cat === c ? palette.ink : "transparent",
                  color: f.cat === c ? palette.paper : palette.inkSoft,
                  border: `1px solid ${f.cat === c ? palette.ink : palette.line}`,
                }}
              >
                {CAT_LABEL[c]}
              </button>
            ))}
          </div>
        </div>

        {f.cat === "color" && (
          <div>
            <label className="text-[11px] block mb-1" style={{ color: palette.inkSoft }}>Muestra de color</label>
            <div className="flex items-center gap-2">
              <input type="color" value={f.swatch} onChange={(e) => set("swatch", e.target.value)} className="w-9 h-9 rounded-sm" style={{ border: `1px solid ${palette.line}`, background: "transparent" }} />
              <span className="font-mono text-xs" style={{ color: palette.inkSoft }}>{f.swatch}</span>
            </div>
          </div>
        )}

        <div>
          <label className="text-[11px] block mb-1" style={{ color: palette.inkSoft }}>
            Término para medir en Google Trends
          </label>
          <input
            value={f.query}
            onChange={(e) => set("query", e.target.value)}
            placeholder={f.name ? f.name.toLowerCase() : "como lo buscaría un cliente"}
            className="w-full text-sm px-2 py-1.5 rounded-sm outline-none"
            style={{ background: palette.paper, color: palette.ink, border: `1px solid ${palette.line}` }}
          />
          <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>
            Escríbelo como lo buscaría un cliente, no como lo llamas internamente.
          </p>
        </div>

        <div>
          <label className="text-[11px] block mb-1" style={{ color: palette.inkSoft }}>Tela o insumo que usas (opcional)</label>
          <input
            value={f.tela}
            onChange={(e) => set("tela", e.target.value)}
            placeholder="Ej. chalis estampado 100 g"
            className="w-full text-sm px-2 py-1.5 rounded-sm outline-none"
            style={{ background: palette.paper, color: palette.ink, border: `1px solid ${palette.line}` }}
          />
        </div>
      </div>

      {/* Evidencia interna */}
      <div className="mt-3 pt-3" style={{ borderTop: `1px dashed ${palette.line}` }}>
        <p className="font-mono text-[10px] uppercase tracking-wide mb-2" style={{ color: palette.inkSoft }}>
          Evidencia interna — reemplaza al dato de Trends mientras no exista
        </p>
        <div className="space-y-2.5">
          {Object.entries(EVIDENCIA).map(([campo, cfg]) => (
            <div key={campo}>
              <p className="text-[11px]" style={{ color: palette.ink }}>{cfg.label}</p>
              <p className="text-[10px] mb-1" style={{ color: palette.inkSoft }}>{cfg.ayuda}</p>
              <div className="flex flex-wrap gap-1.5">
                {cfg.opciones.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => set(campo, o.id)}
                    className="px-2.5 py-1 rounded-full text-xs"
                    style={{
                      background: f[campo] === o.id ? palette.olive : "transparent",
                      color: f[campo] === o.id ? palette.paper : palette.inkSoft,
                      border: `1px solid ${f[campo] === o.id ? palette.olive : palette.line}`,
                    }}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <button
          disabled={!valido}
          onClick={() => onAgregar({ ...f, name: f.name.trim(), query: (f.query || f.name).trim().toLowerCase() })}
          className="px-3 py-1.5 rounded-full text-xs font-medium"
          style={{
            background: valido ? palette.ink : "transparent",
            color: valido ? palette.paper : palette.line,
            border: `1px solid ${valido ? palette.ink : palette.line}`,
            cursor: valido ? "pointer" : "not-allowed",
          }}
        >
          Agregar al radar
        </button>
        <button onClick={onCancelar} className="text-xs" style={{ color: palette.inkSoft }}>
          Cancelar
        </button>
      </div>
    </div>
  );
}

function Autodiagnostico() {
  const [nombre, setNombre] = useState("Mi empresa");
  const [editando, setEditando] = useState(false);
  const [adoptadas, setAdoptadas] = useState([]);
  const [propias, setPropias] = useState([]);
  const [mostrandoForm, setMostrandoForm] = useState(false);
  const [verExport, setVerExport] = useState(false);
  const [detalle, setDetalle] = useState(null);

  const toggle = (id) => setAdoptadas((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const agregarPropia = (datos) => {
    const id = 1000 + propias.length + 1;
    const nueva = { ...datos, id, propia: true, scope: "propia", confianza: "sin medir", code: `PR-${String(propias.length + 1).padStart(2, "0")}` };
    setPropias((prev) => [...prev, nueva]);
    setAdoptadas((prev) => [...prev, id]); // si la agregaste, es porque la trabajas
    setMostrandoForm(false);
  };

  const quitarPropia = (id) => {
    setPropias((prev) => prev.filter((p) => p.id !== id));
    setAdoptadas((prev) => prev.filter((x) => x !== id));
  };

  const r = evaluarEmpresa(adoptadas, propias);

  // Bloque listo para pegar en trends_config.json y que fetch_trends.py
  // empiece a medir estas señales de verdad.
  const exportConfig = JSON.stringify(
    propias.map((p, i) => ({
      id: 100 + i + 1,
      cat: p.cat,
      scope: "propia",
      name: p.name,
      code: p.code,
      ...(p.cat === "color" ? { swatch: p.swatch } : {}),
      query: p.query,
      geo: "CO",
      source: `${nombre} — señal propia, ${new Date().toLocaleDateString("es-CO")}`,
      note: `Agregada desde el autodiagnóstico. Rotación: ${labelDe("rotacion", p.rotacion)}. Mercado: ${labelDe("mercado", p.mercado)}. Proveedor: ${labelDe("proveedor", p.proveedor)}.${p.tela ? ` Tela: ${p.tela}.` : ""}`,
    })),
    null,
    2
  );

  return (
    <div className="mt-10">
      <SectionTitle
        eyebrow="Autodiagnóstico"
        title="Qué tan alineada está tu colección"
        sub="Marca las señales del radar que ya trabajas y agrega las tuyas: los colores, prendas y materiales que vendes y que esta lista no cubre. Con eso el panel calcula tu alineación, te muestra qué estás dejando sobre la mesa y de ahí sale tu lista de telas."
      />

      {/* Nombre de la empresa */}
      <div className="flex items-center gap-2 mb-3">
        {editando ? (
          <input
            autoFocus
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            onBlur={() => setEditando(false)}
            onKeyDown={(e) => e.key === "Enter" && setEditando(false)}
            className="text-lg bg-transparent outline-none border-b"
            style={{ color: palette.ink, borderColor: palette.rust, fontFamily: FONT.ui, fontWeight: 600 }}
          />
        ) : (
          <button onClick={() => setEditando(true)} className="flex items-center gap-1.5 text-lg" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
            {nombre}
            <Pencil size={12} style={{ color: palette.inkSoft }} />
          </button>
        )}
      </div>

      {/* Selector de señales */}
      <div className="card-flat p-4 mb-3">
        <div className="flex items-center justify-between mb-2">
          <p className="font-mono text-[10px] uppercase tracking-wide" style={{ color: palette.inkSoft }}>
            Señales que ya trabajas
          </p>
          {adoptadas.length > 0 && (
            <button onClick={() => setAdoptadas([])} className="text-[11px]" style={{ color: palette.rust }}>
              Limpiar
            </button>
          )}
        </div>
        {["color", "prenda", "material"].map((cat) => {
          const delRadar = TRENDS.filter((t) => t.cat === cat);
          const mias = propias.filter((p) => p.cat === cat);
          return (
            <div key={cat} className="mb-2 last:mb-0">
              <p className="text-[10px] uppercase tracking-wide mb-1" style={{ color: palette.inkSoft }}>{CAT_LABEL[cat]}</p>
              <div className="flex flex-wrap gap-1.5">
                {delRadar.map((t) => {
                  const active = adoptadas.includes(t.id);
                  return (
                    <button
                      key={t.id}
                      onClick={() => toggle(t.id)}
                      className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full"
                      style={{
                        background: active ? palette.ink : "transparent",
                        color: active ? palette.paper : palette.inkSoft,
                        border: `1px solid ${active ? palette.ink : palette.line}`,
                      }}
                    >
                      {active && <Check size={11} />}
                      {t.name}
                    </button>
                  );
                })}
                {mias.map((p) => {
                  const active = adoptadas.includes(p.id);
                  return (
                    <span
                      key={p.id}
                      className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full"
                      style={{
                        background: active ? palette.mustard : "transparent",
                        color: active ? "#fff" : palette.mustard,
                        border: `1px solid ${palette.mustard}`,
                      }}
                    >
                      <button onClick={() => toggle(p.id)} className="flex items-center gap-1">
                        {active && <Check size={11} />}
                        {p.cat === "color" && <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: p.swatch }} />}
                        {p.name}
                      </button>
                      <button onClick={() => quitarPropia(p.id)} aria-label={`Quitar ${p.name}`} style={{ opacity: 0.7 }}>
                        <X size={11} />
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Agregar señal propia */}
      {mostrandoForm ? (
        <FormularioSenal onAgregar={agregarPropia} onCancelar={() => setMostrandoForm(false)} />
      ) : (
        <button
          onClick={() => setMostrandoForm(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
          style={{ color: palette.rust, border: `1px dashed ${palette.rust}` }}
        >
          <Plus size={13} />
          Agregar un color, prenda o material que el radar no cubre
        </button>
      )}

      {adoptadas.length === 0 ? (
        <p className="text-xs" style={{ color: palette.inkSoft }}>
          Marca al menos una señal, o agrega una propia, para ver el diagnóstico.
        </p>
      ) : (
        <>
          {/* Puntaje */}
          <div className="rounded-sm p-4 mb-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `4px solid ${r.nivelColor}` }}>
            <div className="flex items-end justify-between gap-3 flex-wrap">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-wide" style={{ color: palette.inkSoft }}>Alineación con señales comprables</p>
                <p className="font-mono text-4xl leading-none mt-1" style={{ color: r.nivelColor }}>{r.puntaje}<span className="text-lg" style={{ color: palette.inkSoft }}>/100</span></p>
                <p className="text-sm mt-1" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>{r.nivel}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-xl" style={{ color: palette.ink }}>
                  {r.mias.length}<span className="text-xs" style={{ color: palette.inkSoft }}>/{TRENDS.length + propias.length}</span>
                </p>
                <p className="text-[10px] uppercase tracking-wide" style={{ color: palette.inkSoft }}>Señales trabajadas</p>
                {propias.length > 0 && (
                  <p className="text-[10px] mt-0.5" style={{ color: palette.mustard }}>{propias.length} propia{propias.length !== 1 ? "s" : ""}</p>
                )}
              </div>
            </div>
            <div className="mt-3 h-2 rounded-full overflow-hidden" style={{ background: palette.lineSoft }}>
              <div className="h-full rounded-full" style={{ width: `${r.puntaje}%`, background: r.nivelColor }} />
            </div>
            <p className="text-[11px] mt-2 leading-relaxed" style={{ color: palette.inkSoft }}>
              El puntaje promedia la calidad de las señales que trabajas y descuenta hasta 30 puntos por cada señal
              del radar en "Comprar" que estás dejando pasar. Trabajar muchas señales débiles baja el puntaje: la idea
              es concentrar, no acumular.
            </p>
          </div>

          {/* Diagnóstico en tres frentes */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <ListaSenales titulo="Bien apalancado" color={palette.olive} items={r.apalancadas} vacio="Ninguna de tus señales tiene respaldo suficiente para comprar hoy." />
            <ListaSenales titulo="En riesgo — no reponer" color={palette.rust} items={r.enRiesgo} vacio="Nada de lo que trabajas está en caída. Bien." />
            <ListaSenales titulo="Oportunidad sin tomar" color={palette.mustard} items={r.oportunidades} vacio="Estás cubriendo todas las señales comprables del radar." />
          </div>

          {/* Señales propias — lectura provisional */}
          {r.sinMedir.length > 0 && (
            <div className="rounded-sm p-3 mt-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `3px solid ${palette.mustard}` }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold" style={{ color: palette.ink }}>Tus señales propias — lectura provisional</p>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase" style={{ color: palette.mustard, border: `1px solid ${palette.mustard}` }}>
                  sin medir
                </span>
              </div>
              <div className="space-y-1.5">
                {r.sinMedir.map(({ t, dec }) => (
                  <div key={t.id}>
                    <button onClick={() => setDetalle(detalle === t.id ? null : t.id)} className="w-full text-left flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm shrink-0" style={{ color: DECISION_COLOR[dec.label], background: DECISION_BG[dec.label] }}>
                        {dec.score}
                      </span>
                      {t.cat === "color" && <span className="w-3 h-3 rounded-full" style={{ background: t.swatch, border: `1px solid ${palette.line}` }} />}
                      <span className="text-xs" style={{ color: palette.ink }}>{t.name}</span>
                      <span className="text-[10px]" style={{ color: palette.inkSoft }}>· {dec.label} · {CAT_LABEL[t.cat]}</span>
                      <ChevronDown size={12} style={{ color: palette.inkSoft, transform: detalle === t.id ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
                    </button>
                    {detalle === t.id && (
                      <ul className="mt-1 ml-6 space-y-0.5">
                        {dec.reasons.map((x, i) => (
                          <li key={i} className="text-[11px] flex gap-1.5" style={{ color: palette.inkSoft }}>
                            <span>·</span><span>{x}</span>
                          </li>
                        ))}
                        {t.tela && <li className="text-[11px]" style={{ color: palette.ink }}>Tela: {t.tela}</li>}
                        <li className="text-[11px] font-mono" style={{ color: palette.inkSoft }}>Trends: "{t.query}"</li>
                      </ul>
                    )}
                  </div>
                ))}
              </div>
              <p className="text-[11px] mt-2 leading-relaxed" style={{ color: palette.inkSoft }}>
                Estas señales no tienen dato de búsqueda todavía, así que su lectura sale de lo que tú sabes de tu
                propia venta. Por eso ninguna llega a "Comprar": para eso hay que medirlas. Exporta el bloque de abajo,
                pégalo en <code>trends_config.json</code> y la próxima corrida de <code>fetch_trends.py</code> las trae
                con momentum real y entran al radar como cualquier otra.
              </p>

              <div className="mt-2">
                <button onClick={() => setVerExport(!verExport)} className="flex items-center gap-1.5 text-xs font-medium" style={{ color: palette.rust }}>
                  <ChevronDown size={13} style={{ transform: verExport ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
                  Bloque para pegar en trends_config.json ({propias.length})
                </button>
                {verExport && (
                  <pre
                    className="mt-2 p-2 rounded-sm overflow-x-auto text-[10px] leading-relaxed"
                    style={{ background: palette.paper, border: `1px solid ${palette.line}`, color: palette.ink, fontFamily: "'IBM Plex Mono', monospace" }}
                  >
{exportConfig}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* Cobertura por categoría */}
          <div className="card-flat p-4 mt-3">
            <p className="font-mono text-[10px] uppercase tracking-wide mb-2" style={{ color: palette.inkSoft }}>Cobertura por categoría</p>
            <div className="space-y-2">
              {r.cobertura.map((c) => (
                <div key={c.cat}>
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span style={{ color: palette.ink }}>{CAT_LABEL[c.cat]}</span>
                    <span className="font-mono" style={{ color: palette.inkSoft }}>{c.propias}/{c.total}</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: palette.lineSoft }}>
                    <div className="h-full rounded-full" style={{ width: `${c.pct}%`, background: palette.ink }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[11px] mt-2" style={{ color: palette.inkSoft }}>
              Una colección coherente suele cubrir las tres: el color sostiene la vitrina, la prenda define la silueta
              y el material sostiene el precio.
            </p>
          </div>

          {/* Lista de telas derivada */}
          <div className="card-flat p-4 mt-3">
            <p className="font-mono text-[10px] uppercase tracking-wide mb-2" style={{ color: palette.inkSoft }}>
              Telas que se desprenden de tus señales
            </p>
            {r.telas.length === 0 && r.telasPropias.length === 0 ? (
              <p className="text-[11px]" style={{ color: palette.inkSoft }}>Ninguna tela del plan depende de las señales marcadas.</p>
            ) : (
              <div className="space-y-1.5">
                {r.telas.map((m, i) => {
                  const grp = PRESUPUESTO.find((p) => p.id === m.grupo);
                  const resp = respaldoTela(m);
                  return (
                    <div key={i} className="flex items-start gap-2 flex-wrap">
                      <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase shrink-0" style={{ color: grp.color, border: `1px solid ${grp.color}` }}>
                        {grp.label}
                      </span>
                      <span className="text-xs" style={{ color: palette.ink }}>{m.tela}</span>
                      <span className="text-[10px]" style={{ color: palette.inkSoft }}>· {m.consumo} · {resp.label}</span>
                    </div>
                  );
                })}
                {r.telasPropias.map((t, i) => (
                  <div key={`p${i}`} className="flex items-start gap-2 flex-wrap">
                    <span className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase shrink-0" style={{ color: palette.mustard, border: `1px solid ${palette.mustard}` }}>
                      Propia
                    </span>
                    <span className="text-xs" style={{ color: palette.ink }}>{t.tela}</span>
                    <span className="text-[10px]" style={{ color: palette.inkSoft }}>· para {t.senal} · {t.dec.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [filter, setFilter] = useState("todos");
  const [scopeFilter, setScopeFilter] = useState("todos");
  const [onlyReliable, setOnlyReliable] = useState(true);
  const [showLowConf, setShowLowConf] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  const byCat = TRENDS.filter((t) => (filter === "todos" || t.cat === filter) && (scopeFilter === "todos" || t.scope === scopeFilter));
  const reliable = byCat.filter((t) => t.confianza !== "baja");
  const lowConf = byCat.filter((t) => t.confianza === "baja");
  const visible = (onlyReliable ? reliable : byCat)
    .slice()
    .sort((a, b) => {
      const da = computeDecision(a), db = computeDecision(b);
      return DECISION_RANK[da.label] - DECISION_RANK[db.label] || db.score - da.score;
    });
  const upCount = TRENDS.filter((t) => t.dir === "subiendo").length;

  return (
    <div
      className="radar min-h-screen w-full"
      style={{ background: palette.paper, fontFamily: FONT.ui, color: palette.ink }}
    >
      <style>{THEME_CSS}</style>

      {/* Barra de navegación */}
      <div
        className="sticky top-0 z-20"
        style={{ background: palette.paper, borderBottom: `1px solid ${palette.line}` }}
      >
        <div className="max-w-5xl mx-auto px-6 h-12 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 min-w-0">
            <Pin size={13} style={{ color: palette.rust }} />
            <span className="text-xs font-medium truncate" style={{ color: palette.ink }}>Radar de tendencias</span>
            <span className="hidden sm:inline text-xs" style={{ color: palette.inkSoft }}>· ciclo 2026–2027</span>
          </div>
          <nav className="hidden sm:flex items-center gap-5">
            {[
              ["#macro", "Contexto"],
              ["#senales", "Señales"],
              ["#plan", "Plan de compra"],
              ["#criterios", "Criterios"],
              ["#diagnostico", "Diagnóstico"],
            ].map(([href, label]) => (
              <a key={href} href={href} className="navlink">{label}</a>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 pb-20">
        {/* Portada */}
        <header className="pt-14 pb-10">
          <p className="text-[11px] tracking-[0.24em] uppercase mb-5" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
            Investigación de tendencias · plan de compra
          </p>
          <h1
            className="leading-[1.02]"
            style={{ fontFamily: FONT.display, fontWeight: 400, color: palette.ink, fontSize: "clamp(2.6rem, 6.5vw, 4.6rem)", letterSpacing: "-0.02em" }}
          >
            De la señal<br />
            <span style={{ fontStyle: "italic", color: palette.inkSoft }}>a la tela</span>
          </h1>
          <p className="text-base mt-6 max-w-2xl leading-relaxed" style={{ color: palette.inkSoft }}>
            {TRENDS.filter((t) => !t.sinDatosSuficientes).length} de {TRENDS.length} señales con datos de Google Trends,
            cruzadas con Pinterest Predicts y traducidas a una lista de telas. Con la ventana de 24 meses la mayoría de
            las señales locales quedó en confianza baja: el momentum pesa menos que la etiqueta de confianza y las
            búsquedas relacionadas.
          </p>
        </header>

        {/* Color story de la temporada: las señales de color activas, leídas
            como un muestrario de tela — el vocabulario propio del oficio,
            no un adorno genérico. Se recalcula solo del propio TRENDS. */}
        <div className="mb-12">
          <p className="text-[11px] tracking-[0.2em] uppercase mb-4" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
            Color story de la temporada
          </p>
          <div className="flex flex-wrap gap-5">
            {TRENDS.filter((t) => t.cat === "color" && t.swatch).map((t) => (
              <div key={t.id} className="flex flex-col items-center gap-2" style={{ width: 78 }}>
                <span
                  style={{
                    display: "block", width: 44, height: 44, borderRadius: 7, position: "relative",
                    background: t.swatch, boxShadow: "inset 0 0 0 1px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06)",
                  }}
                >
                  <span
                    style={{
                      position: "absolute", top: 5, left: "50%", transform: "translateX(-50%)",
                      width: 5, height: 5, borderRadius: "50%", background: palette.card,
                      boxShadow: "inset 0 0 0 1px rgba(0,0,0,.14)",
                    }}
                  />
                </span>
                <p className="text-center leading-tight" style={{ fontSize: "11px", fontWeight: 500, color: palette.ink }}>{t.name}</p>
                <p className="font-mono text-center" style={{ fontSize: "9px", color: palette.inkSoft, letterSpacing: ".02em" }}>{t.code}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Cifras clave */}
        <div className="grid grid-cols-2 sm:grid-cols-4 hairline" style={{ borderBottom: `1px solid ${palette.line}` }}>
          {[
            { v: TRENDS.length, l: "Señales monitoreadas" },
            { v: upCount, l: "En alza", destacar: true },
            { v: TRENDS.filter((t) => ["Comprar", "Probar en lote pequeño"].includes(computeDecision(t).label)).length, l: "Comprables hoy" },
            { v: MATERIALES.length, l: "Telas en el plan" },
          ].map((k, i) => (
            <div
              key={k.l}
              className="py-6 px-4 first:pl-0"
              style={{ borderLeft: i === 0 ? "none" : `1px solid ${palette.line}` }}
            >
              <p className="num leading-none" style={{ fontFamily: FONT.display, fontSize: "2.6rem", color: k.destacar ? palette.rust : palette.ink }}>
                {k.v}
              </p>
              <p className="text-[11px] uppercase tracking-wider mt-2" style={{ color: palette.inkSoft }}>{k.l}</p>
            </div>
          ))}
        </div>

        {/* Macro context */}
        <div className="mt-12" id="macro">
          <p className="text-[11px] tracking-[0.2em] uppercase mb-3" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
            Contexto macro para comprar
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="card-flat p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium" style={{ color: palette.ink }}>USD/COP</p>
                <Sparkline points={MACRO.usdcop.trayectoria} color={dirColor(MACRO.usdcop.direccion)} />
              </div>
              <p className="font-mono text-xl mt-1" style={{ color: palette.ink }}>
                ${MACRO.usdcop.actual.toLocaleString("es-CO")}
              </p>
              <div className="flex items-center gap-1 text-xs mt-0.5" style={{ color: dirColor(MACRO.usdcop.direccion) }}>
                {dirIcon(MACRO.usdcop.direccion)}
                <span>{MACRO.usdcop.cambio30d > 0 ? "+" : ""}{MACRO.usdcop.cambio30d}% en 30d</span>
              </div>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>
                {MACRO.usdcop.live ? `${MACRO.usdcop.fuente || "TRM oficial · datos.gov.co"} · ${MACRO.usdcop.fechaDato}` : "Valor de referencia — corre fetch_macro.py para el dato real"}
              </p>
            </div>

            <div className="card-flat p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium" style={{ color: palette.ink }}>Algodón (futuros ICE)</p>
                <Sparkline points={MACRO.algodon.trayectoria} color={dirColor(MACRO.algodon.direccion)} />
              </div>
              <p className="font-mono text-xl mt-1" style={{ color: palette.ink }}>
                {MACRO.algodon.actual} <span className="text-xs font-normal" style={{ color: palette.inkSoft }}>{MACRO.algodon.unidad}</span>
              </p>
              <div className="flex items-center gap-1 text-xs mt-0.5" style={{ color: dirColor(MACRO.algodon.direccion) }}>
                {dirIcon(MACRO.algodon.direccion)}
                <span>desde 88 ¢ en mayo</span>
              </div>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO.algodon.fuente}</p>
            </div>

            <div className="card-flat p-4">
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Inflación (IPC)</p>
              <p className="font-mono text-xl mt-1" style={{ color: palette.ink }}>{MACRO_CONTEXT.ipc.anual} <span className="text-xs font-normal" style={{ color: palette.inkSoft }}>anual</span></p>
              <p className="text-xs mt-0.5" style={{ color: palette.inkSoft }}>
                Prendas y calzado: <span style={{ color: palette.ink, fontWeight: 600 }}>+{MACRO_CONTEXT.ipc.sectorPrendas}</span> mensual
              </p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.ipc.fuente}</p>
            </div>

            <div className="rounded-sm p-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `3px solid ${palette.rust}` }}>
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Arancel</p>
              <p className="text-sm mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
                {MACRO_CONTEXT.arancel.titular}
              </p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.arancel.detalle}</p>
              <p className="text-xs mt-1" style={{ color: palette.ink }}>{MACRO_CONTEXT.arancel.accion}</p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.arancel.fuente}</p>
            </div>

            <div className="rounded-sm p-3" style={{ background: palette.card, border: `1px solid ${palette.line}`, borderLeft: `3px solid ${palette.mustard}` }}>
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Materia prima</p>
              <p className="text-sm mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
                {MACRO_CONTEXT.algodonLectura.titular}
              </p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.algodonLectura.detalle}</p>
              <p className="text-xs mt-1" style={{ color: palette.ink }}>{MACRO_CONTEXT.algodonLectura.accion}</p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.algodonLectura.fuente}</p>
            </div>

            <div className="card-flat p-4" style={{ borderLeft: `3px solid ${palette.olive}` }}>
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Región</p>
              <p className="text-sm mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
                {MACRO_CONTEXT.latam.titular}
              </p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.latam.detalle}</p>
              <p className="text-xs mt-1" style={{ color: palette.ink }}>{MACRO_CONTEXT.latam.accion}</p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.latam.fuente}</p>
            </div>

            <div className="card-flat p-4">
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Pasarela regional</p>
              <p className="text-sm mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
                {MACRO_CONTEXT.feriaLatam.nombre}
              </p>
              <p className="text-xs mt-0.5" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.feriaLatam.fecha}</p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.feriaLatam.nota}</p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.feriaLatam.fuente}</p>
            </div>

            <div className="card-flat p-4">
              <p className="text-xs font-medium" style={{ color: palette.ink }}>Próxima feria textil</p>
              <p className="text-sm mt-1 leading-snug" style={{ color: palette.ink, fontFamily: FONT.ui, fontWeight: 600 }}>
                {MACRO_CONTEXT.feria.nombre}
              </p>
              <p className="text-xs mt-0.5" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.feria.fecha}</p>
              <p className="text-[10px] mt-1" style={{ color: palette.inkSoft }}>{MACRO_CONTEXT.feria.fuente}</p>
            </div>
          </div>
        </div>

        {/* Señales */}
        <div className="mt-14">
          <SectionTitle
            eyebrow="El radar"
            title={`Las ${TRENDS.length} señales, ordenadas por decisión`}
            sub="Cada tarjeta trae su puntaje de 0 a 100 y la recomendación que sale de cruzar confianza del dato, momentum, dirección, búsquedas en breakout y corroboración con Pinterest. Filtra por región cuando quieras separar lo que ya pasa aquí de lo que apenas viene llegando."
          />
        </div>

        {/* Decision engine legend */}
        <DecisionLegend />

        {/* Filters */}
        <div className="flex gap-2 mt-5 flex-wrap items-center">
          {CATS.map((c) => (
            <button
              key={c.id}
              onClick={() => setFilter(c.id)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
              style={{
                background: filter === c.id ? palette.ink : "transparent",
                color: filter === c.id ? palette.paper : palette.ink,
                border: `1px solid ${palette.ink}`,
              }}
            >
              {c.label}
            </button>
          ))}
          <span className="w-px h-4 mx-1" style={{ background: palette.line }} />
          <button
            onClick={() => setOnlyReliable(!onlyReliable)}
            className="px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5"
            style={{
              background: "transparent",
              color: onlyReliable ? palette.ink : palette.inkSoft,
              border: `1px solid ${onlyReliable ? palette.ink : palette.line}`,
            }}
          >
            ● Solo confianza media/alta
          </button>
        </div>
        <div className="flex gap-2 mt-2 flex-wrap items-center">
          {SCOPES.map((sc) => (
            <button
              key={sc.id}
              onClick={() => setScopeFilter(sc.id)}
              className="px-3 py-1.5 rounded-full text-xs"
              style={{
                background: "transparent",
                color: scopeFilter === sc.id ? palette.ink : palette.inkSoft,
                border: `1px solid ${scopeFilter === sc.id ? palette.ink : palette.line}`,
              }}
            >
              {sc.label}
            </button>
          ))}
        </div>

        {onlyReliable && lowConf.length > 0 && (
          <p className="text-[11px] mt-2" style={{ color: palette.inkSoft }}>
            {lowConf.length} señal{lowConf.length !== 1 ? "es" : ""} de confianza baja oculta{lowConf.length !== 1 ? "s" : ""} — visibles como contexto al final del panel.
          </p>
        )}

        {/* Grid */}
        <div id="senales" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
          {visible.map((t) => (
            <div key={t.id} className={expandedId === t.id ? "sm:col-span-2 lg:col-span-3" : ""}>
              <SwatchCard
                trend={t}
                expanded={expandedId === t.id}
                onToggle={() => setExpandedId(expandedId === t.id ? null : t.id)}
              />
            </div>
          ))}
        </div>

        {onlyReliable && lowConf.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowLowConf(!showLowConf)}
              className="flex items-center gap-1.5 text-xs font-medium"
              style={{ color: palette.inkSoft }}
            >
              <ChevronDown size={13} style={{ transform: showLowConf ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
              Contexto: {lowConf.length} señal{lowConf.length !== 1 ? "es" : ""} de confianza baja (no usar para decidir)
            </button>
            {showLowConf && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {lowConf.map((t) => (
                  <span
                    key={t.id}
                    className="text-xs px-2 py-1 rounded-sm"
                    style={{ color: palette.inkSoft, border: `1px dashed ${palette.line}`, opacity: 0.75 }}
                  >
                    {t.name} · {t.momentum}/100 · {t.dir}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Plan de materiales — del radar a la orden de compra */}
        <div id="plan"><PlanMateriales /></div>

        {/* Criterios, calendario y métricas */}
        <div id="criterios"><CriteriosYCalendario /></div>

        {/* Pinterest Predicts — annual reference */}
        <div className="mt-10">
          <p className="font-mono text-[11px] tracking-[0.2em] uppercase mb-1" style={{ color: palette.inkSoft }}>
            Referencia anual · {PINTEREST_PREDICTS.edicion}
          </p>
          <h2 className="text-xl mb-1" style={{ fontFamily: FONT.ui, fontWeight: 600, color: palette.ink }}>
            Pinterest Predicts
          </h2>
          <p className="text-xs mb-4" style={{ color: palette.inkSoft }}>
            {PINTEREST_PREDICTS.precision}. Se actualiza una vez al año, cuando sale el próximo reporte (normalmente en diciembre).
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {PINTEREST_PREDICTS.items.map((it, i) => (
              <div key={i} className="card-flat p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold" style={{ color: palette.ink, fontFamily: FONT.ui }}>{it.name}</p>
                  <span
                    className="font-mono text-[9px] px-1.5 py-0.5 rounded-sm uppercase shrink-0"
                    style={{ color: palette.inkSoft, border: `1px solid ${palette.line}` }}
                  >
                    {it.cat}
                  </span>
                </div>
                <p className="text-xs mt-1 leading-relaxed" style={{ color: palette.inkSoft }}>{it.note}</p>
                {it.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {it.keywords.map((k, j) => (
                      <span key={j} className="font-mono text-[10px] px-1.5 py-0.5 rounded-sm" style={{ color: palette.rust, border: `1px solid ${palette.rust}` }}>
                        {k.t} {k.g}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Autodiagnóstico de la empresa */}
        <div id="diagnostico"><Autodiagnostico /></div>

        {/* Pie */}
        <footer className="mt-16 pt-6" style={{ borderTop: `1px solid ${palette.line}` }}>
          <div className="flex flex-wrap gap-x-10 gap-y-4 justify-between">
            <div className="max-w-md">
              <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
                Cómo leer este panel
              </p>
              <p className="text-xs leading-relaxed" style={{ color: palette.inkSoft }}>
                El momentum viene de Google Trends: es interés de búsqueda relativo de 0 a 100, no ventas ni volumen
                absoluto. Ninguna recomendación reemplaza el sell-through de tu propia tienda; el panel ordena señales
                dispersas para que la conversación de compra empiece con datos y no con intuición.
              </p>
            </div>
            <div>
              <p className="text-[11px] tracking-[0.2em] uppercase mb-2" style={{ color: palette.inkSoft, fontFamily: FONT.mono }}>
                Actualización
              </p>
              <ul className="text-xs space-y-1" style={{ color: palette.inkSoft }}>
                <li>Señales · <code>fetch_trends.py</code> cada 1–2 semanas</li>
                <li>Tasa de cambio · <code>fetch_macro.py</code></li>
                <li>Pinterest Predicts · anual, cada diciembre</li>
                <li>IPC y arancel · revisión trimestral</li>
              </ul>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
