import { DemandaTipo } from "@/lib/types-coordinacion";
import { num } from "@/lib/format";

/** Texto «164 con alternativa afín (→ Apoyo entre pares)» de una fila de demanda. */
export function textoDesvio(d: DemandaTipo): string {
  if (d.atendidos_con_alternativa === 0) return "Ninguno";
  const destinos = d.destinos
    .map((x) => `${x.tipo_label}: ${num(x.cantidad, 0)}`)
    .join(", ");
  return `${num(d.atendidos_con_alternativa, 0)} → ${destinos}`;
}

/**
 * Demanda real por tipo de servicio. Un pedido «atendido con alternativa afín» pedía un tipo y
 * terminó en otro: así se ve la demanda de consejería aunque la ocupación de sus servicios
 * parezca media.
 */
export default function DemandaPorTipo({ demanda }: { demanda: DemandaTipo[] }) {
  return (
    <div className="overflow-hidden rounded-xl2 border border-aura-border bg-white shadow-card">
      <div className="border-b border-aura-border px-6 py-4">
        <p className="font-bold text-aura-navy">Demanda real por tipo de servicio</p>
        <p className="mt-1 text-sm text-aura-gray">
          Pedidos según el servicio que necesitaban. «Con alternativa afín» son los
          que terminaron en otro tipo porque el ideal no tenía cupo compatible.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-aura-bg text-xs font-bold uppercase tracking-wide text-aura-gray">
            <tr>
              <th className="px-6 py-3">Servicio ideal</th>
              <th className="px-4 py-3">Pedidos</th>
              <th className="px-4 py-3">En su tipo</th>
              <th className="px-4 py-3">Con alternativa afín (a cuál)</th>
              <th className="px-4 py-3">Sin cupo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-aura-border">
            {demanda.map((d) => (
              <tr key={d.ideal}>
                <td className="px-6 py-3.5 font-semibold text-aura-navy">{d.ideal_label}</td>
                <td className="px-4 py-3.5 text-aura-navy">{num(d.pedidos, 0)}</td>
                <td className="px-4 py-3.5 text-aura-navy">{num(d.atendidos_en_su_tipo, 0)}</td>
                <td className="px-4 py-3.5 text-aura-navy">{textoDesvio(d)}</td>
                <td className="px-4 py-3.5 text-aura-navy">{num(d.sin_cupo, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
