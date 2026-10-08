"use client";

import { FiltrosServicios, ServicioFeature } from "@/lib/types-coordinacion";
import FiltroSelect from "../FiltroSelect";

/** Mini leyenda de las letras de los puntos: C, A, O = tipo de servicio (inicial de su nombre). */
export function LeyendaTipos({ todos }: { todos: ServicioFeature[] }) {
  const tipos = new Map<string, string>();
  todos.forEach(({ properties: p }) => tipos.set(p.tipo, p.tipo_label));
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-semibold text-co-navy" aria-label="Significado de las letras">
      {[...tipos.values()].sort().map((label) => (
        <li key={label} className="flex items-center gap-1.5">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-co-teal-tint text-[11px] font-extrabold text-co-teal-dark">
            {label.charAt(0)}
          </span>
          {label}
        </li>
      ))}
    </ul>
  );
}

/**
 * Filtros del mapa: tipo de servicio (las opciones salen de los servicios del backend; al cambiar,
 * se vuelve a consultar) y «solo alta demanda». No hay filtro por canal: no aporta en el mapa.
 */
export default function FiltrosMapa({
  todos,
  filtros,
  onChange,
}: {
  todos: ServicioFeature[];
  filtros: FiltrosServicios;
  onChange: (filtros: FiltrosServicios) => void;
}) {
  const tipos = new Map<string, string>();
  todos.forEach(({ properties: p }) => tipos.set(p.tipo, p.tipo_label));
  const activos = Boolean(filtros.tipo || filtros.solo_alta_demanda);

  return (
    <div className="flex flex-wrap items-end gap-x-5 gap-y-3">
      <div className="w-full max-w-xs">
        <FiltroSelect
          etiqueta="Tipo de servicio"
          valor={filtros.tipo ?? ""}
          opciones={[...tipos].map(([valor, label]) => ({ valor, label }))}
          onChange={(tipo) => onChange({ ...filtros, tipo: tipo || undefined })}
        />
      </div>
      <label className="flex cursor-pointer items-center gap-2 pb-2 text-sm font-bold text-co-navy">
        <input
          type="checkbox"
          checked={Boolean(filtros.solo_alta_demanda)}
          onChange={(e) =>
            onChange({ ...filtros, solo_alta_demanda: e.target.checked || undefined })
          }
          className="co-foco h-4 w-4 rounded border-co-line accent-[#1B5E66]"
        />
        Solo alta demanda
      </label>
      <button
        type="button"
        onClick={() => onChange({})}
        disabled={!activos}
        className="co-foco pb-2 text-sm font-bold text-co-teal disabled:cursor-default disabled:text-co-ink/50"
      >
        Limpiar
      </button>
      <div className="ml-auto pb-2">
        <LeyendaTipos todos={todos} />
      </div>
    </div>
  );
}
