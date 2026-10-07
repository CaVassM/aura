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
    <div className="rounded-xl2 border border-aura-border bg-white p-4 shadow-card sm:p-5">
      <div className="flex flex-wrap items-end gap-4">
        <FiltroSelect
          etiqueta="Motivo"
          valor={filtros.motivo ?? ""}
          opciones={reglas.motivo_servicio.items.map((m) => ({
            valor: m.motivo,
            label: m.motivo_label,
          }))}
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
          valor={filtros.servicio_ideal ?? ""}
          opciones={reglas.afinidad.tipos.map((t) => ({ valor: t.codigo, label: t.label }))}
          onChange={poner("servicio_ideal")}
        />
        <FiltroSelect
          etiqueta="Grupo"
          valor={filtros.grupo ?? ""}
          opciones={GRUPOS}
          onChange={poner("grupo")}
        />
        <button
          type="button"
          onClick={() => onChange({})}
          disabled={!activos}
          className="pb-2 text-sm font-semibold text-aura-teal disabled:cursor-default disabled:text-aura-gray-light"
        >
          Limpiar
        </button>
        <a
          href={urlDesencuentrosCsv(filtros)}
          download="desencuentros.csv"
          aria-disabled={filtrados === 0}
          className={`ml-auto inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold ${
            filtrados === 0
              ? "pointer-events-none border-aura-border text-aura-gray-light"
              : "border-aura-teal text-aura-teal hover:bg-aura-teal-pale"
          }`}
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Exportar CSV
        </a>
      </div>
      <p className="mt-3 text-xs text-aura-gray">
        La tabla, el heatmap y el hallazgo se actualizan juntos.
      </p>
    </div>
  );
}
