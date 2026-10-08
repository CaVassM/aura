"use client";

import { Download } from "lucide-react";
import { urlDesencuentrosCsv } from "@/lib/api";
import { distritoLabel } from "@/lib/format";
import { FiltrosDesencuentros, Reglas, ServicioFeature } from "@/lib/types-coordinacion";
import FiltroSelect from "../FiltroSelect";

// El grupo es la única lista fija: son los dos valores que define el motor.
const GRUPOS = [
  { valor: "diurno", label: "Diurno" },
  { valor: "nocturno", label: "Nocturno" },
];

/**
 * Filtros de Desencuentros. Motivos y servicios ideales salen de `reglas`, distritos de los
 * servicios (D6). Incluye «Exportar CSV» con los mismos filtros.
 */
export default function FiltrosDesencuentrosBarra({
  reglas,
  servicios,
  filtros,
  onChange,
  filtrados,
}: {
  reglas: Reglas;
  servicios: ServicioFeature[];
  filtros: FiltrosDesencuentros;
  onChange: (filtros: FiltrosDesencuentros) => void;
  filtrados: number;
}) {
  const distritos = [...new Set(servicios.map((s) => s.properties.distrito))].sort();
  const activos = Object.values(filtros).some(Boolean);
  const poner = (campo: keyof FiltrosDesencuentros) => (valor: string) =>
    onChange({ ...filtros, [campo]: valor || undefined });

  return (
    <div className="flex flex-wrap items-end gap-x-5 gap-y-3">
      <FiltroSelect
        etiqueta="Motivo"
        valor={filtros.motivo ?? ""}
        opciones={reglas.motivo_servicio.items.map((m) => ({ valor: m.motivo, label: m.motivo_label }))}
        onChange={poner("motivo")}
      />
      <FiltroSelect
        etiqueta="Distrito"
        valor={filtros.distrito ?? ""}
        opciones={distritos.map((d) => ({ valor: d, label: distritoLabel(d) }))}
        onChange={poner("distrito")}
      />
      <FiltroSelect
        etiqueta="Servicio ideal"
        termino="servicio_ideal"
        valor={filtros.servicio_ideal ?? ""}
        opciones={reglas.afinidad.tipos.map((t) => ({ valor: t.codigo, label: t.label }))}
        onChange={poner("servicio_ideal")}
      />
      <FiltroSelect
        etiqueta="Grupo"
        termino="grupo"
        valor={filtros.grupo ?? ""}
        opciones={GRUPOS}
        onChange={poner("grupo")}
      />
      <button
        type="button"
        onClick={() => onChange({})}
        disabled={!activos}
        className="co-foco pb-2 text-sm font-bold text-co-teal disabled:cursor-default disabled:text-co-ink/50"
      >
        Limpiar
      </button>
      <a
        href={urlDesencuentrosCsv(filtros)}
        download="desencuentros.csv"
        aria-disabled={filtrados === 0}
        className={`co-foco ml-auto inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-bold ${
          filtrados === 0
            ? "pointer-events-none bg-co-line/60 text-co-ink/60"
            : "bg-co-teal text-white hover:bg-co-teal-dark"
        }`}
      >
        <Download className="h-4 w-4" aria-hidden="true" />
        Exportar CSV
      </a>
    </div>
  );
}
