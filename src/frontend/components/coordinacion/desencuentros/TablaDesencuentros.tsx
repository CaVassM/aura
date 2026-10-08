"use client";

import { Desencuentro } from "@/lib/types-coordinacion";
import { distritoLabel, fechaCorta } from "@/lib/format";
import { ConInfo } from "../InfoTip";

/**
 * Tabla paginada de desencuentros. La franja y el grupo se muestran tal como los manda el
 * backend; nunca se deducen del horario.
 */
export default function TablaDesencuentros({
  items,
  total,
  pagina,
  paginas,
  tamano,
  onPagina,
}: {
  items: Desencuentro[];
  total: number;
  pagina: number;
  paginas: number;
  tamano: number;
  onPagina: (pagina: number) => void;
}) {
  const desde = (pagina - 1) * tamano + 1;
  const hasta = Math.min(total, pagina * tamano);
  const boton =
    "co-foco rounded-md border border-co-line px-3 py-1.5 text-sm font-bold text-co-navy transition-colors hover:bg-co-teal-tint disabled:cursor-default disabled:text-co-ink/50 disabled:hover:bg-transparent";
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[920px] text-left text-sm">
          <thead>
            <tr className="border-b-2 border-co-navy/80 text-xs font-extrabold text-co-navy">
              <th className="py-2.5 pr-4">Fecha</th>
              <th className="px-3 py-2.5">Motivo</th>
              <th className="px-3 py-2.5">
                <ConInfo termino="servicio_ideal">Servicio ideal</ConInfo>
              </th>
              <th className="px-3 py-2.5">Distrito</th>
              <th className="px-3 py-2.5">
                <ConInfo termino="franja">Franja</ConInfo>
              </th>
              <th className="px-3 py-2.5">Canales aceptados</th>
              <th className="py-2.5 pl-3">
                <ConInfo termino="grupo">Grupo</ConInfo>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-co-line">
            {items.map((d) => (
              <tr key={d.id} className="animate-fade-only transition-colors hover:bg-co-teal-tint/50">
                <td className="whitespace-nowrap py-3 pr-4 font-semibold text-co-navy">{fechaCorta(d.fecha)}</td>
                <td className="px-3 py-3 font-bold text-co-navy">{d.motivo_label}</td>
                <td className="px-3 py-3 font-semibold text-co-teal">{d.servicio_ideal_label}</td>
                <td className="px-3 py-3 font-medium text-co-navy">{distritoLabel(d.distrito)}</td>
                <td className="whitespace-nowrap px-3 py-3 font-medium text-co-navy">
                  {d.franja.dia} · {d.franja.desde}–{d.franja.hasta}
                </td>
                <td className="px-3 py-3 font-medium text-co-ink">{d.canales_label.join(", ")}</td>
                <td className="py-3 pl-3">
                  <span
                    className={`inline-flex items-center gap-1.5 text-xs font-bold ${d.grupo === "nocturno" ? "text-co-teal" : "text-co-amber-ink"}`}
                  >
                    <span
                      className={`h-2 w-2 rounded-full ${d.grupo === "nocturno" ? "bg-co-teal" : "bg-co-amber"}`}
                      aria-hidden="true"
                    />
                    {d.grupo_label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-co-line pt-3 text-sm font-medium text-co-ink">
        <span>
          Mostrando <span className="tabular font-bold text-co-navy">{desde}–{hasta}</span> de{" "}
          <span className="tabular font-bold text-co-navy">{total}</span>
        </span>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => onPagina(pagina - 1)} disabled={pagina <= 1} className={boton}>
            Anterior
          </button>
          <span aria-live="polite" className="tabular font-bold text-co-navy">
            Página {pagina} de {paginas}
          </span>
          <button type="button" onClick={() => onPagina(pagina + 1)} disabled={pagina >= paginas} className={boton}>
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}
