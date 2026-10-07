import { Desencuentro } from "@/lib/types-coordinacion";
import { distritoLabel, fechaCorta } from "@/lib/format";
import Tag from "@/components/ui/Tag";

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
  return (
    <div className="overflow-hidden rounded-xl2 border border-aura-border bg-white shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[920px] text-left text-sm">
          <thead className="bg-aura-bg text-xs font-bold uppercase tracking-wide text-aura-gray">
            <tr>
              <th className="px-5 py-3">Fecha</th>
              <th className="px-4 py-3">Motivo</th>
              <th className="px-4 py-3">Servicio ideal</th>
              <th className="px-4 py-3">Distrito</th>
              <th className="px-4 py-3">Franja</th>
              <th className="px-4 py-3">Canales aceptados</th>
              <th className="px-5 py-3">Grupo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-aura-border">
            {items.map((d) => (
              <tr key={d.id} className="hover:bg-aura-bg/60">
                <td className="whitespace-nowrap px-5 py-3.5 text-aura-navy">
                  {fechaCorta(d.fecha)}
                </td>
                <td className="px-4 py-3.5 font-medium text-aura-navy">
                  {d.motivo_label}
                </td>
                <td className="px-4 py-3.5 text-aura-navy">{d.servicio_ideal_label}</td>
                <td className="px-4 py-3.5 text-aura-navy">{distritoLabel(d.distrito)}</td>
                <td className="whitespace-nowrap px-4 py-3.5 text-aura-navy">
                  {d.franja.dia} · {d.franja.desde}–{d.franja.hasta}
                </td>
                <td className="px-4 py-3.5 text-aura-gray">
                  {d.canales_label.join(", ")}
                </td>
                <td className="px-5 py-3.5">
                  <Tag variant={d.grupo === "nocturno" ? "purple" : "green"}>
                    {d.grupo_label}
                  </Tag>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-aura-border px-5 py-3 text-sm text-aura-gray">
        <span>
          Mostrando {desde}–{hasta} de {total}
        </span>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => onPagina(pagina - 1)}
            disabled={pagina <= 1}
            className="rounded-lg border border-aura-border px-3 py-1.5 font-medium text-aura-navy hover:bg-aura-bg disabled:cursor-default disabled:text-aura-gray-light disabled:hover:bg-transparent"
          >
            Anterior
          </button>
          <span aria-live="polite">
            Página {pagina} de {paginas}
          </span>
          <button
            type="button"
            onClick={() => onPagina(pagina + 1)}
            disabled={pagina >= paginas}
            className="rounded-lg border border-aura-border px-3 py-1.5 font-medium text-aura-navy hover:bg-aura-bg disabled:cursor-default disabled:text-aura-gray-light disabled:hover:bg-transparent"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}
