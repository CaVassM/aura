"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import { ServicioFeature } from "@/lib/types-coordinacion";
import { distritoLabel } from "@/lib/format";
import Barra from "../Barra";
import EmbudoCupos, { EncabezadoEmbudo } from "../EmbudoCupos";
import { ConInfo } from "../InfoTip";
import NombreServicio, { NivelTag } from "../NombreServicio";
import { NIVEL_BG, NIVEL_INK } from "../nivel";
import NumeroAnimado from "../NumeroAnimado";
import { useDemo } from "../DemoProvider";

/** Tabla de servicios: embudo de cupos por fila y orden por ocupación. Un clic abre el drawer. */
export default function TablaServicios({
  servicios,
  seleccionadoId,
  orden,
  onOrden,
  onSelect,
}: {
  servicios: ServicioFeature[];
  seleccionadoId: string | null;
  orden: "asc" | "desc";
  onOrden: () => void;
  onSelect: (id: string) => void;
}) {
  const { estado } = useDemo();
  const semanas = estado ? `${estado.agenda_abierta_semanas} semanas` : "agenda abierta";
  const ordenados = [...servicios].sort((a, b) =>
    orden === "desc"
      ? b.properties.ocupacion_pct - a.properties.ocupacion_pct
      : a.properties.ocupacion_pct - b.properties.ocupacion_pct,
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1080px] text-left text-sm">
        <thead>
          <tr className="border-b-2 border-co-navy/80 align-bottom text-xs font-extrabold text-co-navy">
            <th className="min-w-[17rem] py-3 pr-4">Servicio</th>
            <th className="px-3 py-3">Distrito</th>
            <th className="px-3 py-3">
              <ConInfo termino="capacidad_semanal">Capacidad semanal (D6)</ConInfo>
            </th>
            <th className="min-w-[26rem] px-3 py-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-co-teal">
                Embudo de cupos · {semanas}
              </p>
              <EncabezadoEmbudo />
            </th>
            <th className="min-w-[13rem] py-3 pl-3" aria-sort={orden === "desc" ? "descending" : "ascending"}>
              <button
                type="button"
                onClick={onOrden}
                className="co-foco inline-flex items-center gap-1 rounded text-xs font-extrabold text-co-navy hover:text-co-teal"
                title="Cambiar el orden por ocupación"
              >
                Ocupación
                {orden === "desc" ? <ArrowDown className="h-3.5 w-3.5" /> : <ArrowUp className="h-3.5 w-3.5" />}
              </button>
              <ConInfo termino="nivel">{""}</ConInfo>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-co-line">
          {ordenados.map(({ properties: p }) => (
            <tr
              key={p.service_id}
              tabIndex={0}
              onClick={() => onSelect(p.service_id)}
              onKeyDown={(e) => e.key === "Enter" && onSelect(p.service_id)}
              className={`co-foco cursor-pointer align-top transition-colors hover:bg-co-teal-tint/60 ${p.service_id === seleccionadoId ? "bg-co-teal-tint/70" : ""}`}
            >
              <td className="py-4 pr-4">
                <NombreServicio nombre={p.nombre} tipoLabel={p.tipo_label} apilado />
                <p className="mt-1 text-xs font-medium text-co-ink">
                  {p.horario_texto} · {p.canales_label.join(", ")}
                </p>
              </td>
              <td className="px-3 py-4 font-bold text-co-navy">{distritoLabel(p.distrito)}</td>
              <td className="tabular px-3 py-4 font-bold text-co-navy">{p.capacidad_semanal}</td>
              <td className="px-3 py-4">
                <EmbudoCupos
                  variante="fila"
                  datos={{
                    capacidad: p.capacidad_agenda_abierta,
                    libres: p.libres_agenda_abierta,
                    liberados: p.cupos_liberados,
                    reservados: p.cupos_reservados,
                  }}
                />
              </td>
              <td className="py-4 pl-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Barra pct={p.ocupacion_pct} color={NIVEL_BG[p.nivel]} alto="h-2.5" />
                  </div>
                  <span className={`w-16 text-right text-base font-extrabold ${NIVEL_INK[p.nivel]}`}>
                    <NumeroAnimado valor={p.ocupacion_pct} decimales={1} sufijo="%" duracion={600} />
                  </span>
                </div>
                <div className="mt-1.5">
                  <NivelTag nivel={p.nivel} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
