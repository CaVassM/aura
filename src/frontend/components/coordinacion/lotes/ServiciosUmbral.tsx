import { distritoLabel, num } from "@/lib/format";
import { ServicioLote } from "@/lib/types-coordinacion";

/** Cuánto antes del umbral se marca un servicio como «cerca». */
const CERCA_PTS = 5;

/**
 * Utilización de cada servicio con el umbral de modo lote marcado en la barra. En naranja/coral, los que ya
 * están en modo lote (sus cupos solo se reparten por lote); en ámbar, los que están a punto de llegar.
 */
export default function ServiciosUmbral({ servicios, umbralPct }: { servicios: ServicioLote[]; umbralPct: number }) {
  return (
    <ul className="divide-y divide-co-line overflow-hidden rounded-2xl border border-co-line bg-co-paper shadow-card">
      {servicios.map((s, i) => {
        const cerca = !s.en_lote && s.pct >= umbralPct - CERCA_PTS;
        const color = s.en_lote ? "bg-co-coral" : cerca ? "bg-co-amber" : "bg-co-teal";
        const ink = s.en_lote ? "text-co-coral-ink" : cerca ? "text-co-amber-ink" : "text-co-ink";
        return (
          <li
            key={s.service_id}
            className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1.5 px-5 py-3 animate-fade-in lg:grid-cols-[15rem_1fr_9rem]"
            style={{ animationDelay: `${i * 25}ms` }}
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-bold text-co-navy">{s.nombre}</p>
              <p className="text-xs font-semibold text-co-teal">
                {s.tipo_label} · {distritoLabel(s.distrito)}
              </p>
            </div>

            <div className="relative col-span-2 h-3 lg:col-span-1">
              <div className="absolute inset-0 overflow-hidden rounded-full bg-co-line/70">
                <div
                  className={`h-full origin-left rounded-full animate-grow-x transition-[width] duration-700 ease-out ${color}`}
                  style={{ width: `${Math.min(100, s.pct)}%` }}
                />
              </div>
              {/* marca del umbral */}
              <span
                className="absolute -top-1 bottom-[-4px] w-0.5 rounded bg-co-navy/70"
                style={{ left: `${umbralPct}%` }}
                title={`Umbral de modo lote: ${num(umbralPct)} %`}
                aria-hidden="true"
              />
            </div>

            <div className="row-start-1 justify-self-end text-right lg:row-start-auto">
              <p className={`tabular text-lg font-extrabold leading-none ${ink}`}>{num(s.pct)} %</p>
              <p className="mt-0.5 flex items-center justify-end gap-1.5 text-[11px] font-semibold text-co-ink/80">
                {s.en_lote && (
                  <span className="rounded bg-co-coral px-1.5 py-0.5 text-[10px] font-extrabold uppercase leading-none tracking-wider text-white">
                    en lote
                  </span>
                )}
                {cerca && (
                  <span className="rounded bg-co-amber-tint px-1.5 py-0.5 text-[10px] font-extrabold uppercase leading-none tracking-wider text-co-amber-ink">
                    cerca
                  </span>
                )}
                <span className="tabular">
                  {s.reservados}/{s.liberados}
                </span>
              </p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
