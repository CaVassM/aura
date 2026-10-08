"use client";

import { Termino } from "@/lib/glosario";
import InfoTip from "./InfoTip";

export interface OpcionFiltro {
  valor: string;
  label: string;
}

/** Select de filtro con opción «Todos» (y un ⓘ opcional junto a la etiqueta). */
export default function FiltroSelect({
  etiqueta,
  valor,
  opciones,
  onChange,
  textoTodos = "Todos",
  termino,
}: {
  etiqueta: string;
  valor: string;
  opciones: OpcionFiltro[];
  onChange: (valor: string) => void;
  textoTodos?: string;
  termino?: Termino;
}) {
  return (
    <div className="flex min-w-[10rem] flex-1 flex-col gap-1">
      <div className="flex items-center text-xs font-bold text-co-navy">
        {etiqueta}
        {termino && <InfoTip termino={termino} />}
      </div>
      <select
        aria-label={`Filtrar por ${etiqueta.toLowerCase()}`}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        className="co-foco rounded-md border border-co-line bg-co-paper px-3 py-2 text-sm font-semibold text-co-navy transition-colors hover:border-co-teal"
      >
        <option value="">{textoTodos}</option>
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
