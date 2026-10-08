"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Route } from "lucide-react";
import { ServicioFeature, ServicioProps } from "@/lib/types-coordinacion";
import { distritoLabel, pct } from "@/lib/format";
import EmbudoCupos from "../EmbudoCupos";
import { LeyendaNiveles } from "../resumen/GraficoOcupacion";
import EstadoVacioMapa from "./EstadoVacioMapa";
import { NIVEL_FILL, NIVEL_INK, NIVEL_LABEL } from "../nivel";

// Tintes suaves y distintos para cada distrito.
const TINTES = [
  { fill: "#DCEBE8", stroke: "#9CC4BD" }, // teal
  { fill: "#F8E9C6", stroke: "#DDBE74" }, // ámbar
  { fill: "#FBE3DB", stroke: "#E4A793" }, // coral
  { fill: "#DDEDE4", stroke: "#9CC7AF" }, // salvia
  { fill: "#E6E1F0", stroke: "#B5A9D1" }, // lavanda
];

const ANCHO_TIP = 288; // w-72
const ALTO_TIP = 236; // estimado: nombre, tipo, horario, % y embudo mini
const clamp = (v: number, min: number, max: number) => Math.min(Math.max(v, min), max);

/** Polígono irregular (octágono con radios variados) alrededor de un centro; determinista. */
function poligono(cx: number, cy: number, indice: number, escala: number): string {
  const puntos = [];
  for (let k = 0; k < 8; k++) {
    const ang = (k * Math.PI) / 4 + Math.PI / 8;
    const variacion = 1 + 0.14 * Math.sin(k * 1.9 + indice * 2.3);
    puntos.push(
      `${(cx + Math.cos(ang) * 175 * escala * variacion).toFixed(1)},${(cy + Math.sin(ang) * 112 * escala * variacion).toFixed(1)}`,
    );
  }
  return puntos.join(" ");
}

interface Colocado extends Punto {
  p: ServicioProps;
}

interface Punto {
  x: number;
  y: number;
  r: number;
}

/** ¿El rectángulo toca el círculo (con un margen)? */
function tocaPunto(rect: { left: number; top: number }, pt: Punto, margen = 8): boolean {
  const cx = clamp(pt.x, rect.left, rect.left + ANCHO_TIP);
  const cy = clamp(pt.y, rect.top, rect.top + ALTO_TIP);
  return Math.hypot(pt.x - cx, pt.y - cy) < pt.r + 5 + margen;
}

/**
 * Coloca el globo junto al punto SIN tapar ningún punto (ni el suyo ni sus vecinos) y dentro del
 * mapa. Prueba posiciones en orden de cercanía: arriba‑izquierda, abajo‑derecha, a los lados y
 * arriba/abajo, alejándose del punto lo justo para librar a los demás puntos del distrito.
 */
function colocarGlobo(m: Punto, puntos: Punto[], ancho: number, alto: number) {
  const g = 10;
  const dentro = (left: number, top: number) => ({
    left: clamp(left, 8, Math.max(8, ancho - ANCHO_TIP - 8)),
    top: clamp(top, 8, Math.max(8, alto - ALTO_TIP - 8)),
  });
  const candidatos: { left: number; top: number }[] = [];
  for (let extra = 0; extra <= 220; extra += 22) {
    const d = m.r + g + extra;
    candidatos.push(
      dentro(m.x - d - ANCHO_TIP, m.y + 4 - ALTO_TIP), // arriba‑izquierda
      dentro(m.x + d, m.y - 4), // abajo‑derecha
      dentro(m.x + d, m.y - ALTO_TIP / 2), // a la derecha
      dentro(m.x - d - ANCHO_TIP, m.y - ALTO_TIP / 2), // a la izquierda
      dentro(m.x - ANCHO_TIP / 2, m.y - d - ALTO_TIP), // arriba
      dentro(m.x - ANCHO_TIP / 2, m.y + d), // abajo
    );
  }
  const libre = candidatos.find((c) => !puntos.some((pt) => tocaPunto(c, pt)));
  return libre ?? candidatos[0];
}

/**
 * Ciudad ilustrada con distritos como polígonos de tinte suave y un punto por servicio. El mapa
 * se proyecta al tamaño real del contenedor (se reajusta si el drawer lo estrecha). Tamaño del
 * punto = capacidad semanal (D6), color = nivel de ocupación, halo = alta demanda.
 */
export default function MapaCiudad({
  todos,
  visibles,
  seleccionadoId,
  onSelect,
  onLimpiarFiltros,
}: {
  todos: ServicioFeature[];
  visibles: ServicioFeature[];
  seleccionadoId: string | null;
  onSelect: (id: string) => void;
  onLimpiarFiltros: () => void;
}) {
  const contenedor = useRef<HTMLDivElement>(null);
  const [dim, setDim] = useState({ w: 1100, h: 640 });
  const [tip, setTip] = useState<Colocado | null>(null);

  useEffect(() => {
    const el = contenedor.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => {
      const { width, height } = e.contentRect;
      if (width > 0 && height > 0) setDim({ w: width, h: height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { w, h } = dim;
  const padX = Math.max(96, w * 0.1);
  const padArriba = Math.max(120, h * 0.2);
  const padAbajo = Math.max(84, h * 0.13);

  const proyectar = (p: ServicioProps) => ({
    x: padX + p.pos.x * (w - 2 * padX),
    y: padArriba + p.pos.y * (h - padArriba - padAbajo),
  });

  const { distritos, escala, minCap, maxCap } = useMemo(() => {
    const porDistrito = new Map<string, { x: number; y: number }[]>();
    const caps: number[] = [];
    todos.forEach((f) => {
      const pt = proyectar(f.properties);
      const lista = porDistrito.get(f.properties.distrito) ?? [];
      lista.push(pt);
      porDistrito.set(f.properties.distrito, lista);
      caps.push(f.properties.capacidad_semanal);
    });
    const lista = [...porDistrito.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([id, puntos], i) => ({
        id,
        x: puntos.reduce((s, p) => s + p.x, 0) / puntos.length,
        y: puntos.reduce((s, p) => s + p.y, 0) / puntos.length,
        tinte: TINTES[i % TINTES.length],
        indice: i,
      }));
    // Escala: que los polígonos vecinos no se pisen aunque el mapa se estreche.
    let dmin = Infinity;
    lista.forEach((a, i) =>
      lista.slice(i + 1).forEach((b) => {
        dmin = Math.min(dmin, Math.hypot(a.x - b.x, a.y - b.y));
      }),
    );
    return {
      distritos: lista,
      escala: Number.isFinite(dmin) ? clamp(dmin / 300, 0.5, 1.1) : 1,
      minCap: Math.min(...caps),
      maxCap: Math.max(...caps),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [todos, w, h]);

  const radio = (capacidad: number) =>
    (13 + (maxCap > minCap ? ((capacidad - minCap) / (maxCap - minCap)) * 13 : 6)) * clamp(escala, 0.75, 1.1);

  const puntos: Punto[] = visibles.map((f) => ({
    ...proyectar(f.properties),
    r: radio(f.properties.capacidad_semanal),
  }));
  const globo = tip ? colocarGlobo(tip, puntos, w, h) : null;

  return (
    <div
      ref={contenedor}
      className="relative h-[calc(100vh-15rem)] min-h-[520px] w-full overflow-hidden rounded-lg border border-co-line bg-[#EEF4F1]"
    >
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="absolute inset-0 h-full w-full"
        role="img"
        aria-label="Mapa ilustrativo de los distritos de Aethera"
      >
        <defs>
          <pattern id="cuadricula" width="38" height="38" patternUnits="userSpaceOnUse">
            <path d="M 38 0 L 0 0 0 38" fill="none" stroke="#D5E4DF" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={w} height={h} fill="url(#cuadricula)" />

        {/* Distritos: polígonos rellenos */}
        {distritos.map((d) => (
          <polygon
            key={d.id}
            points={poligono(d.x, d.y, d.indice, escala)}
            fill={d.tinte.fill}
            stroke={d.tinte.stroke}
            strokeWidth={3}
            strokeLinejoin="round"
          />
        ))}

        {/* Calles decorativas (se estiran con el mapa) */}
        <g transform={`scale(${w / 1520} ${h / 800})`}>
          <g fill="none" stroke="#FFFFFF" strokeLinecap="round" opacity={0.85}>
            <path d="M60 560 C420 470 760 520 1120 330 S1400 210 1470 190" strokeWidth={14} />
            <path d="M140 150 C420 260 620 360 860 470 S1260 640 1460 660" strokeWidth={10} />
            <path d="M700 30 C760 220 700 440 780 770" strokeWidth={8} />
          </g>
          <g fill="none" stroke="#9FBFB7" strokeDasharray="8 10" strokeWidth={2}>
            <path d="M60 575 C420 485 760 535 1120 345 S1400 225 1470 205" />
            <path d="M140 165 C420 275 620 375 860 485 S1260 655 1460 675" />
          </g>
        </g>

        {/* Nombres de distrito, por encima de las calles */}
        {distritos.map((d) => (
          <text
            key={d.id}
            x={d.x}
            y={d.y - 128 * escala}
            textAnchor="middle"
            fontSize={clamp(24 * escala, 16, 26)}
            fontWeight={800}
            fill="#1D2E3C"
            stroke="#FFFFFF"
            strokeWidth={6}
            paintOrder="stroke"
            strokeLinejoin="round"
          >
            {distritoLabel(d.id)}
          </text>
        ))}

        {/* Servicios */}
        {visibles.map((f, i) => {
          const p = f.properties;
          const { x, y } = proyectar(p);
          const r = radio(p.capacidad_semanal);
          const elegido = p.service_id === seleccionadoId;
          const colocado: Colocado = { p, x, y, r };
          return (
            <g key={p.service_id} transform={`translate(${x} ${y})`}>
              <g className="svg-centro animate-pop-in" style={{ animationDelay: `${i * 55}ms` }}>
                {p.nivel === "alta" && (
                  <circle
                    r={r + 4}
                    className="halo-pulso svg-centro animate-halo fill-co-coral"
                    style={{ animationDelay: `${(i % 5) * 400}ms` }}
                  />
                )}
                <g
                  role="button"
                  tabIndex={0}
                  aria-label={`${p.nombre}, ${p.tipo_label}, ${pct(p.ocupacion_pct)} de ocupación, nivel ${NIVEL_LABEL[p.nivel].toLowerCase()}`}
                  onClick={() => onSelect(p.service_id)}
                  onFocus={() => setTip(colocado)}
                  onBlur={() => setTip(null)}
                  onMouseEnter={() => setTip(colocado)}
                  onMouseLeave={() => setTip(null)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(p.service_id);
                    }
                  }}
                  className="svg-centro cursor-pointer outline-none transition-transform duration-200 hover:scale-110 focus-visible:scale-110"
                >
                  <circle r={r + 5} fill="#FFFFFF" opacity={0.95} />
                  {elegido && <circle r={r + 9} fill="none" strokeWidth={3} className="stroke-co-teal" />}
                  <circle r={r} className={NIVEL_FILL[p.nivel]} />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fontSize={r > 20 ? 15 : 13}
                    fontWeight={800}
                    className="fill-co-navy"
                    pointerEvents="none"
                  >
                    {p.tipo_label.charAt(0)}
                  </text>
                </g>
              </g>
            </g>
          );
        })}
      </svg>

      {tip && globo && (
        <div
          role="tooltip"
          className="pointer-events-none absolute z-20 animate-fade-only rounded-md border border-co-line bg-co-paper p-3 shadow-pop"
          style={{ left: globo.left, top: globo.top, width: ANCHO_TIP }}
        >
          <p className="font-extrabold leading-tight text-co-navy">{tip.p.nombre}</p>
          <p className="text-xs font-bold text-co-teal">{tip.p.tipo_label}</p>
          <p className="mt-1.5 text-xs font-medium text-co-ink">{tip.p.horario_texto}</p>
          <p className="mt-2 flex items-baseline gap-2">
            <span className={`tabular text-xl font-extrabold ${NIVEL_INK[tip.p.nivel]}`}>
              {pct(tip.p.ocupacion_pct)}
            </span>
            <span className={`text-xs font-bold ${NIVEL_INK[tip.p.nivel]}`}>
              ocupación · {NIVEL_LABEL[tip.p.nivel].toLowerCase()}
            </span>
          </p>
          <div className="mt-2.5 border-t border-co-line pt-2.5">
            <EmbudoCupos
              variante="mini"
              datos={{
                capacidad: tip.p.capacidad_agenda_abierta,
                libres: tip.p.libres_agenda_abierta,
                liberados: tip.p.cupos_liberados,
                reservados: tip.p.cupos_reservados,
              }}
            />
          </div>
        </div>
      )}

      <div className="absolute bottom-4 right-4 rounded-md border border-co-line bg-co-paper/95 p-3 text-xs shadow-card backdrop-blur">
        <div className="mb-2 flex items-center gap-2 font-extrabold text-co-navy">
          <Route className="h-4 w-4 text-co-teal" aria-hidden="true" />
          Cómo leer el mapa
        </div>
        <LeyendaNiveles />
        <p className="mt-2 font-medium text-co-ink">
          Tamaño del punto = capacidad semanal (D6). Halo = alta demanda.
        </p>
      </div>

      {visibles.length === 0 && <EstadoVacioMapa onLimpiar={onLimpiarFiltros} />}
    </div>
  );
}
