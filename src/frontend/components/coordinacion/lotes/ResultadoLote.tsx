import { CheckCircle2, Equal } from "lucide-react";
import { bloqueFecha, distritoLabel, num, rangoHoras } from "@/lib/format";
import { LoteDetalle, MetricasLote } from "@/lib/types-coordinacion";

function Columna({ titulo, m, mejor }: { titulo: string; m: MetricasLote; mejor: boolean }) {
  const filas: [string, string][] = [
    ["Asignadas", String(m.asignados)],
    ["Sin cupo", String(m.desencuentros)],
    ["Espera media", `${num(m.espera_media)} d`],
    ["Espera diurnos", `${num(m.espera_diurnos)} d`],
    ["Espera nocturnos", `${num(m.espera_nocturnos)} d`],
    ["Objetivo (menor es mejor)", num(m.objetivo, 3)],
  ];
  return (
    <div className={`rounded-xl border px-4 py-3 ${mejor ? "border-co-teal bg-co-teal-tint/50" : "border-co-line bg-white"}`}>
      <p className="flex items-center gap-2 text-sm font-extrabold text-co-navy">
        {titulo}
        {mejor && (
          <span className="inline-flex items-center gap-1 rounded bg-co-teal px-1.5 py-0.5 text-[10px] font-extrabold uppercase leading-none tracking-wider text-white">
            <CheckCircle2 size={10} aria-hidden="true" /> mejor
          </span>
        )}
      </p>
      <dl className="mt-2 space-y-1 text-xs">
        {filas.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3">
            <dt className="font-semibold text-co-ink">{k}</dt>
            <dd className="tabular font-bold text-co-navy">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** Un lote ya resuelto: qué le tocó a cada solicitud y cómo quedó frente a asignar por orden de llegada. */
export default function ResultadoLote({ lote }: { lote: LoteDetalle }) {
  const r = lote.resultado;
  if (!r) return null;
  if (r.error) {
    return <p className="rounded-xl bg-co-coral-tint px-4 py-3 text-sm font-semibold text-co-coral-ink">No se pudo resolver el lote: {r.error}</p>;
  }
  const ga = r.genetico;
  const llegada = r.llegada;
  return (
    <div className="space-y-4">
      {ga && llegada && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Columna titulo="Algoritmo genético" m={ga} mejor={!!r.mejora_sobre_llegada} />
          <Columna titulo="Orden de llegada" m={llegada} mejor={false} />
        </div>
      )}
      {ga && !r.mejora_sobre_llegada && (
        <p className="flex items-start gap-2 text-xs font-medium leading-relaxed text-co-ink">
          <Equal size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
          El resultado es el mismo que asignando por orden de llegada: las solicitudes no competían por los mismos
          cupos. El genético solo cambia el orden cuando eso reparte mejor (más asignadas, menos espera o más equidad).
        </p>
      )}

      <ul className="divide-y divide-co-line overflow-hidden rounded-xl border border-co-line bg-white">
        {r.asignaciones
          .slice()
          .sort((a, b) => a.orden_asignacion - b.orden_asignacion)
          .map((a) => {
            const f = bloqueFecha(a.fecha);
            return (
              <li key={a.cita_id} className="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-1 px-4 py-3 text-sm lg:grid-cols-[3rem_9rem_1fr_14rem]">
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-full bg-co-teal-tint text-xs font-extrabold text-co-teal-dark"
                  title={`Prioridad ${a.orden_asignacion} del genético (llegó ${a.posicion_llegada}º)`}
                >
                  {a.orden_asignacion}
                </span>
                <span className="font-bold text-co-navy">{a.estudiante_id}</span>
                <span className="min-w-0 col-span-2 lg:col-span-1">
                  <span className="block truncate font-bold text-co-navy">
                    {a.servicio_nombre}
                    <span className="text-xs font-semibold text-co-teal"> · {a.tipo_label}</span>
                  </span>
                  <span className="text-xs font-semibold text-co-ink">
                    {a.canal_label}
                    {a.canal === "in_person" && ` · ${distritoLabel(a.distrito)}`}
                    {a.es_alternativa && <span className="text-co-amber-ink"> · servicio alternativo</span>}
                  </span>
                </span>
                <span className="tabular col-span-2 text-xs font-semibold text-co-ink lg:col-span-1 lg:text-right">
                  {f.dia} {f.numero} {f.mes} · {rangoHoras(a.hora_inicio, a.hora_fin)} · espera {a.espera_dias} d · {a.cita_id}
                </span>
              </li>
            );
          })}
        {r.sin_cupo_estudiantes.map((id) => (
          <li key={id} className="flex items-center gap-3 bg-co-amber-tint/60 px-4 py-3 text-sm">
            <span className="rounded bg-co-amber px-1.5 py-0.5 text-[10px] font-extrabold uppercase leading-none tracking-wider text-white">sin cupo</span>
            <span className="font-bold text-co-navy">{id}</span>
            <span className="text-xs font-semibold text-co-amber-ink">Quedó como desencuentro; ya se le avisó.</span>
          </li>
        ))}
      </ul>

      <p className="text-[11px] font-semibold text-co-ink/80">
        Genético · {r.poblacion} individuos × {r.generaciones} generaciones · {num(r.tiempo_s ?? 0, 2)} s. Si no mejora el orden de
        llegada, se conserva el de llegada.
      </p>
    </div>
  );
}
