"use client";

export interface OpcionFiltro {
  valor: string;
  label: string;
}

/** Select de filtro con opción «Todos». */
export default function FiltroSelect({
  etiqueta,
  valor,
  opciones,
  onChange,
  textoTodos = "Todos",
}: {
  etiqueta: string;
  valor: string;
  opciones: OpcionFiltro[];
  onChange: (valor: string) => void;
  textoTodos?: string;
}) {
  return (
    <label className="flex min-w-[10rem] flex-1 flex-col gap-1 text-xs font-semibold text-aura-gray">
      {etiqueta}
      <select
        aria-label={`Filtrar por ${etiqueta.toLowerCase()}`}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-xl border border-aura-border bg-white px-3 py-2 text-sm font-medium text-aura-navy focus:border-aura-teal focus:outline-none"
      >
        <option value="">{textoTodos}</option>
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
