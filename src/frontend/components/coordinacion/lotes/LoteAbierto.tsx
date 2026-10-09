import { Loader2, PackagePlus } from "lucide-react";
import { distritoLabel } from "@/lib/format";
import { LoteDetalle } from "@/lib/types-coordinacion";
import { mmss, useCuentaRegresiva } from "./useCuentaRegresiva";

/** El lote que está esperando solicitudes: cuenta regresiva, cuántas lleva y quiénes son. Se cierra solo. */
export default function LoteAbierto({
  lote,
  ventanaS,
  tamanoMaximo,
  servidorAhora,
}: {
  lote: LoteDetalle;
  ventanaS: number;
  tamanoMaximo: number;
  servidorAhora: string;
}) {
  const restante = useCuentaRegresiva(lote.cierra_en, servidorAhora) ?? 0;
  const asignando = lote.estado === "resolviendo" || restante <= 0;
  const pctTiempo = Math.min(100, Math.max(0, (100 * restante) / ventanaS));

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-co-teal to-co-teal-deep p-6 text-white shadow-lift animate-rise">
      <span className="pointer-events-none absolute -right-8 -top-10 h-40 w-40 rounded-full bg-white/10" aria-hidden="true" />
      <div className="relative flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal-tint">
            <PackagePlus size={14} aria-hidden="true" />
            Lote {lote.id} · abierto
          </p>
          <p className="mt-2 text-5xl font-extrabold tracking-tight tabular">
            {asignando ? (
              <span className="flex items-center gap-3 text-3xl">
                <Loader2 className="animate-spin" size={28} aria-hidden="true" />
                Asignando en conjunto…
              </span>
            ) : (
              mmss(restante)
            )}
          </p>
          <p className="mt-1 text-sm text-co-teal-tint">
            {asignando ? "El algoritmo genético reparte los cupos entre todas las solicitudes." : "Se cierra solo cuando llegue a cero o al juntar el máximo."}
          </p>
        </div>
        <div className="text-right">
          <p className="tabular text-4xl font-extrabold leading-none">
            {lote.solicitudes.length}
            <span className="text-2xl font-bold text-co-teal-tint"> / {tamanoMaximo}</span>
          </p>
          <p className="mt-1 text-xs font-bold uppercase tracking-wider text-co-teal-tint">solicitudes</p>
        </div>
      </div>

      <div className="relative mt-5 h-2 overflow-hidden rounded-full bg-white/15" role="img" aria-label={`Tiempo restante ${mmss(restante)}`}>
        <div className="h-full rounded-full bg-co-amber transition-[width] duration-300 ease-linear" style={{ width: `${asignando ? 0 : pctTiempo}%` }} />
      </div>

      <ul className="relative mt-5 divide-y divide-white/10 rounded-xl bg-white/10">
        {lote.solicitudes.map((s) => (
          <li key={s.posicion} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 text-sm animate-fade-in">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs font-extrabold text-co-teal-deep">
              {s.posicion}
            </span>
            <span className="font-bold">{s.estudiante_id}</span>
            <span className="text-co-teal-tint">{s.motivo_label}</span>
            <span className="text-co-teal-tint">· {distritoLabel(s.distrito)}</span>
            <span className="text-co-teal-tint">· {s.grupo_label}</span>
            <span className="tabular ml-auto text-xs text-co-teal-tint">
              {new Date(s.entrada_en).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
