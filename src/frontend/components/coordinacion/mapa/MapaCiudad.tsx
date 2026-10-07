"use client";

import { useMemo, useState } from "react";
import { Route } from "lucide-react";
import { ServicioFeature, ServicioProps } from "@/lib/types-coordinacion";
import { distritoLabel, pct } from "@/lib/format";
import EstadoVacioMapa from "./EstadoVacioMapa";
import LeyendaNiveles from "../LeyendaNiveles";
import { NIVEL_FILL, NIVEL_LABEL } from "../nivel";

// Lienzo del mapa ilustrado (viewBox) y márgenes donde caen los puntos normalizados `pos` 0–1.
const ANCHO = 1000;
const ALTO = 740;
const MARGEN_X = 110;
const MARGEN_Y = 120;

const posicion = (p: ServicioProps) => ({
  x: MARGEN_X + p.pos.x * (ANCHO - 2 * MARGEN_X),
  y: MARGEN_Y + p.pos.y * (ALTO - 2 * MARGEN_Y),
});

// Colores suaves de los distritos (decorativo).
const MANCHAS = [
  { fill: "#E6F4F0", stroke: "#B6DCD3" },
  { fill: "#F4F3E9", stroke: "#DED8B9" },
  { fill: "#FDEEEA", stroke: "#EBC9BF" },
  { fill: "#EAF0FB", stroke: "#C5D3EE" },
  { fill: "#F2ECE7", stroke: "#DAC7B7" },
];

/**
 * Ciudad ilustrada (calles y cuadrícula decorativas) con un marcador por servicio.
 * Posición, nivel y datos vienen del backend; los distritos se dibujan alrededor de los
 * servicios que contienen (`todos`), así no cambian al filtrar.
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
  const [hover, setHover] = useState<ServicioProps | null>(null);

  const distritos = useMemo(() => {
    const porDistrito = new Map<string, { x: number; y: number }[]>();
    todos.forEach((f) => {
      const lista = porDistrito.get(f.properties.distrito) ?? [];
      lista.push(posicion(f.properties));
      porDistrito.set(f.properties.distrito, lista);
    });
    return [...porDistrito.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([id, puntos], i) => ({
        id,
        x: puntos.reduce((s, p) => s + p.x, 0) / puntos.length,
        y: puntos.reduce((s, p) => s + p.y, 0) / puntos.length,
        color: MANCHAS[i % MANCHAS.length],
      }));
  }, [todos]);

  const iniciales = useMemo(() => {
    const porTipo = new Map<string, string>();
    todos.forEach((f) => porTipo.set(f.properties.tipo, f.properties.tipo_label));
    return [...porTipo.values()].sort();
  }, [todos]);

  return (
    <div className="relative aspect-[1.35/1] min-h-[260px] w-full bg-aura-teal-pale sm:min-h-[380px]">
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        className="absolute inset-0 h-full w-full"
        role="img"
        aria-label="Mapa ilustrativo de los distritos de Aethera"
      >
        <defs>
          <pattern id="aether-grid" width="34" height="34" patternUnits="userSpaceOnUse">
            <path d="M 34 0 L 0 0 0 34" fill="none" stroke="#dce9e5" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={ANCHO} height={ALTO} fill="url(#aether-grid)" />

        {distritos.map((d) => (
          <g key={d.id}>
            <ellipse
              cx={d.x}
              cy={d.y}
              rx={105}
              ry={85}
              fill={d.color.fill}
              stroke={d.color.stroke}
              strokeWidth={3}
            />
          </g>
        ))}

        <g fill="none" stroke="#FFFFFF" strokeLinecap="round">
          <path d="M100 190 C290 200 400 390 880 520" strokeWidth={16} />
          <path d="M180 610 C350 470 570 360 900 190" strokeWidth={12} />
          <path d="M470 40 C505 220 450 390 500 685" strokeWidth={9} />
          <path d="M55 420 C280 410 690 310 930 330" strokeWidth={7} />
        </g>
        <g fill="none" stroke="#AFC6C1" strokeDasharray="8 10" strokeWidth={2}>
          <path d="M88 212 C340 250 560 465 925 505" />
          <path d="M205 638 C340 510 650 395 900 235" />
        </g>

        {distritos.map((d) => (
          <text
            key={d.id}
            x={d.x}
            y={d.y - 98}
            textAnchor="middle"
            fontSize={19}
            fontWeight={700}
            fill="#536276"
            stroke="#FFFFFF"
            strokeWidth={5}
            paintOrder="stroke"
          >
            {distritoLabel(d.id)}
          </text>
        ))}

        {visibles.map((f) => {
          const p = f.properties;
          const { x, y } = posicion(p);
          const elegido = p.service_id === seleccionadoId;
          return (
            <g
              key={p.service_id}
              role="button"
              tabIndex={0}
              aria-label={`${p.nombre}, ${p.tipo_label}, ${pct(p.ocupacion_pct)} de ocupación, nivel ${NIVEL_LABEL[p.nivel].toLowerCase()}`}
              onClick={() => onSelect(p.service_id)}
              onFocus={() => setHover(p)}
              onBlur={() => setHover(null)}
              onMouseEnter={() => setHover(p)}
              onMouseLeave={() => setHover(null)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect(p.service_id);
                }
              }}
              className="cursor-pointer outline-none"
            >
              <circle
                cx={x}
                cy={y}
                r={elegido ? 24 : 19}
                fill="white"
                opacity={0.9}
                className={elegido ? "stroke-aura-teal" : ""}
                strokeWidth={elegido ? 3 : 0}
              />
              <circle
                cx={x}
                cy={y}
                r={14}
                stroke="white"
                strokeWidth={3}
                className={NIVEL_FILL[p.nivel]}
              />
              <text
                x={x}
                y={y + 5}
                textAnchor="middle"
                fontSize={12}
                fontWeight={700}
                className="fill-aura-navy"
              >
                {p.tipo_label.charAt(0)}
              </text>
            </g>
          );
        })}
      </svg>

      {hover && (
        <div
          className="pointer-events-none absolute z-10 max-w-72 rounded-xl border border-aura-border bg-white p-3 text-xs shadow-card"
          style={{
            left: `${(posicion(hover).x / ANCHO) * 100}%`,
            top: `${(posicion(hover).y / ALTO) * 100}%`,
            transform: "translate(12px, -110%)",
          }}
        >
          <div className="font-bold text-aura-navy">{hover.nombre}</div>
          <div className="mt-1 text-aura-gray">
            {hover.tipo_label} · {distritoLabel(hover.distrito)}
          </div>
          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-aura-gray">
            <span>{hover.horario_texto}</span>
            <span>{hover.canales_label.join(", ")}</span>
            <span>Capacidad semanal: {hover.capacidad_semanal}</span>
            <span>Liberados: {hover.cupos_liberados}</span>
            <span>Ocupados: {hover.cupos_ocupados}</span>
            <span className="font-bold text-aura-navy">
              {pct(hover.ocupacion_pct)} · {NIVEL_LABEL[hover.nivel]}
            </span>
          </div>
        </div>
      )}

      <div className="absolute bottom-4 right-4 rounded-xl border border-aura-border bg-white/95 p-3 text-xs shadow-sm backdrop-blur">
        <div className="mb-2 flex items-center gap-2 font-bold text-aura-navy">
          <Route className="h-4 w-4 text-aura-teal" aria-hidden="true" />
          Leyenda
        </div>
        <LeyendaNiveles className="flex-col !items-start gap-1.5" />
        {iniciales.length > 0 && (
          <div className="mt-2 border-t border-aura-border pt-2 text-aura-gray">
            {iniciales.map((t) => `${t.charAt(0)} ${t}`).join(" · ")}
          </div>
        )}
      </div>

      {visibles.length === 0 && (
        <EstadoVacioMapa onLimpiar={onLimpiarFiltros} />
      )}
    </div>
  );
}
