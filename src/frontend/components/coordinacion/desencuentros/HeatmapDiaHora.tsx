import { Heatmap } from "@/lib/types-coordinacion";

/** Heatmap día × hora: cuántas solicitudes sin cupo cubren cada hora (sobre el conjunto filtrado). */
export default function HeatmapDiaHora({ heatmap }: { heatmap: Heatmap }) {
  const { dias, horas, celdas } = heatmap;
  const maximo = Math.max(1, ...celdas.flat());

  return (
    <div className="rounded-xl2 border border-aura-border bg-white p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-bold text-aura-navy">
            Cuándo buscan cita quienes no encuentran cupo
          </p>
          <p className="mt-1 text-sm text-aura-gray">
            Solicitudes sin cupo compatible por día y hora (franja que declaró
            cada persona). Se actualiza con los filtros.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-aura-gray">
          Menos
          <span
            className="h-2.5 w-24 rounded-full"
            style={{
              background:
                "linear-gradient(to right, rgba(40,91,99,0.12), rgba(40,91,99,1))",
            }}
          />
          Más ({maximo})
        </div>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-1 text-center text-xs">
          <thead>
            <tr>
              <th className="w-12" />
              {horas.map((h) => (
                <th key={h} scope="col" className="pb-1 font-semibold text-aura-gray">
                  {h}h
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dias.map((dia, i) => (
              <tr key={dia}>
                <th scope="row" className="pr-2 text-right font-semibold text-aura-navy">
                  {dia}
                </th>
                {horas.map((hora, j) => {
                  const valor = celdas[i]?.[j] ?? 0;
                  const alfa = valor === 0 ? 0 : 0.12 + 0.88 * (valor / maximo);
                  return (
                    <td
                      key={hora}
                      aria-label={`${dia}, ${hora}:00: ${valor} desencuentros`}
                      title={`${dia} ${hora}:00 · ${valor} desencuentros`}
                      className={`h-9 rounded-md font-semibold ${valor === 0 ? "bg-aura-bg text-transparent" : ""} ${alfa > 0.55 ? "text-white" : "text-aura-navy"}`}
                      style={
                        valor === 0
                          ? undefined
                          : { backgroundColor: `rgba(40,91,99,${alfa})` }
                      }
                    >
                      {valor === 0 ? "·" : valor}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
