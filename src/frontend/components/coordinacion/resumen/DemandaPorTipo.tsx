"use client";

import { DemandaTipo } from "@/lib/types-coordinacion";
import { num } from "@/lib/format";
import { ConInfo } from "../InfoTip";

/** Texto «164 → Apoyo entre pares: 164» de una fila de demanda. */
export function textoDesvio(d: DemandaTipo): string {
  if (d.atendidos_con_alternativa === 0) return "Ninguno";
  const destinos = d.destinos.map((x) => `${x.tipo_label}: ${num(x.cantidad, 0)}`).join(", ");
  return `${num(d.atendidos_con_alternativa, 0)} → ${destinos}`;
}

/**
 * Demanda real por tipo de servicio. Un pedido «atendido con alternativa afín» pedía un tipo y
 * terminó en otro: así se ve la demanda de consejería aunque la ocupación de sus servicios
 * parezca media.
 */
export default function DemandaPorTipo({ demanda }: { demanda: DemandaTipo[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b-2 border-co-navy/80 text-xs font-extrabold text-co-navy">
            <th className="py-2.5 pr-4">
              <ConInfo termino="servicio_ideal">Servicio ideal</ConInfo>
            </th>
            <th className="px-4 py-2.5">
              <ConInfo termino="pedidos">Pedidos</ConInfo>
            </th>
            <th className="px-4 py-2.5">
              <ConInfo termino="en_su_tipo">En su tipo</ConInfo>
            </th>
            <th className="px-4 py-2.5">
              <ConInfo termino="atendidos_alternativa">Con alternativa afín (a cuál)</ConInfo>
            </th>
            <th className="py-2.5 pl-4">
              <ConInfo termino="desencuentros">Sin cupo</ConInfo>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-co-line">
          {demanda.map((d) => (
            <tr key={d.ideal}>
              <td className="py-3.5 pr-4 font-bold text-co-navy">{d.ideal_label}</td>
              <td className="tabular px-4 py-3.5 font-semibold text-co-navy">{num(d.pedidos, 0)}</td>
              <td className="tabular px-4 py-3.5 font-semibold text-co-navy">{num(d.atendidos_en_su_tipo, 0)}</td>
              <td
                className={`tabular px-4 py-3.5 font-bold ${d.atendidos_con_alternativa ? "text-co-teal" : "text-co-ink"}`}
              >
                {textoDesvio(d)}
              </td>
              <td
                className={`tabular py-3.5 pl-4 font-bold ${d.sin_cupo ? "text-co-coral-ink" : "text-co-ink"}`}
              >
                {num(d.sin_cupo, 0)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
