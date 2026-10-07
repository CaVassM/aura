"use client";

import { FiltrosServicios, ServicioFeature } from "@/lib/types-coordinacion";
import FiltroSelect from "../FiltroSelect";

/** Filtros del mapa. Las opciones salen de los servicios del backend; al cambiar, se vuelve a consultar. */
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
  const canales = new Map<string, string>();
  todos.forEach(({ properties: p }) => {
    tipos.set(p.tipo, p.tipo_label);
    p.canales.forEach((c, i) => canales.set(c, p.canales_label[i]));
  });
  const activos = Boolean(filtros.tipo || filtros.canal || filtros.solo_alta_demanda);

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl2 border border-aura-border bg-white p-4 shadow-card sm:p-5">
      <FiltroSelect
        etiqueta="Tipo de servicio"
        valor={filtros.tipo ?? ""}
        opciones={[...tipos].map(([valor, label]) => ({ valor, label }))}
        onChange={(tipo) => onChange({ ...filtros, tipo: tipo || undefined })}
      />
      <FiltroSelect
        etiqueta="Canal"
        valor={filtros.canal ?? ""}
        opciones={[...canales].map(([valor, label]) => ({ valor, label }))}
        onChange={(canal) => onChange({ ...filtros, canal: canal || undefined })}
      />
      <label className="flex items-center gap-2 pb-2 text-sm font-medium text-aura-navy">
        <input
          type="checkbox"
          checked={Boolean(filtros.solo_alta_demanda)}
          onChange={(e) =>
            onChange({ ...filtros, solo_alta_demanda: e.target.checked || undefined })
          }
          className="h-4 w-4 rounded border-aura-border accent-[#285B63]"
        />
        Solo alta demanda
      </label>
      <button
        type="button"
        onClick={() => onChange({})}
        disabled={!activos}
        className="pb-2 text-sm font-semibold text-aura-teal disabled:cursor-default disabled:text-aura-gray-light"
      >
        Limpiar
      </button>
    </div>
  );
}
