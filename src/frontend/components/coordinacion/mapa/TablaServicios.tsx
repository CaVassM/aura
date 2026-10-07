import { ServicioFeature } from "@/lib/types-coordinacion";
import { distritoLabel, pct } from "@/lib/format";
import NombreServicio, { NivelTag } from "../NombreServicio";
import { NIVEL_BG } from "../nivel";

/** Tabla «Servicios y cupos liberados»: lo mismo que ven los marcadores, en filas. */
export default function TablaServicios({
  servicios,
  seleccionadoId,
  onSelect,
}: {
  servicios: ServicioFeature[];
  seleccionadoId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl2 border border-aura-border bg-white shadow-card">
      <div className="border-b border-aura-border px-5 py-4">
        <p className="font-bold text-aura-navy">Servicios y cupos liberados</p>
        <p className="mt-1 text-sm text-aura-gray">
          Capacidad semanal, horarios y uso de cupos liberados de la agenda
          abierta. Selecciona un servicio para ver su detalle.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[960px] text-left text-sm">
          <thead className="bg-aura-bg text-xs font-bold uppercase tracking-wide text-aura-gray">
            <tr>
              <th className="px-5 py-3">Servicio</th>
              <th className="px-4 py-3">Distrito</th>
              <th className="px-4 py-3">Capacidad semanal</th>
              <th className="px-4 py-3">Liberados</th>
              <th className="px-4 py-3">Ocupados</th>
              <th className="min-w-56 px-5 py-3">Ocupación</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-aura-border">
            {servicios.map(({ properties: p }) => (
              <tr
                key={p.service_id}
                onClick={() => onSelect(p.service_id)}
                className={`cursor-pointer align-top hover:bg-aura-bg/60 ${p.service_id === seleccionadoId ? "bg-aura-teal-pale/50" : ""}`}
              >
                <td className="px-5 py-4">
                  <NombreServicio nombre={p.nombre} tipoLabel={p.tipo_label} apilado />
                  <p className="mt-1 text-xs text-aura-gray">
                    {p.horario_texto} · {p.canales_label.join(", ")}
                  </p>
                  {p.direccion && (
                    <p className="mt-1 text-xs text-aura-gray">{p.direccion}</p>
                  )}
                </td>
                <td className="px-4 py-4 font-semibold text-aura-navy">
                  {distritoLabel(p.distrito)}
                </td>
                <td className="px-4 py-4 text-aura-navy">{p.capacidad_semanal}</td>
                <td className="px-4 py-4 text-aura-navy">{p.cupos_liberados}</td>
                <td className="px-4 py-4 text-aura-navy">{p.cupos_ocupados}</td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-aura-bg">
                      <div
                        className={`h-full rounded-full ${NIVEL_BG[p.nivel]}`}
                        style={{ width: `${Math.min(100, p.ocupacion_pct)}%` }}
                      />
                    </div>
                    <span className="w-12 text-right font-bold text-aura-navy">
                      {pct(p.ocupacion_pct)}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <NivelTag nivel={p.nivel} />
                    {p.alta_demanda && (
                      <span className="text-[11px] font-bold text-aura-tag-red-text">
                        Alta demanda
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
