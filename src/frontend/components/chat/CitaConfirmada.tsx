import Link from "next/link";
import { ArrowRight, CalendarClock, Clock, MapPin, X } from "lucide-react";
import { fechaConDia, primeraMayuscula, rangoHoras } from "@/lib/format";
import { nombreDistrito } from "@/lib/perfiles";
import { canalUi, estiloServicio } from "@/lib/servicios-ui";
import { Cita } from "@/lib/types";

function datosCita(cita: Cita) {
  const [fecha, hora] = cita.slot.fecha_iso.split("T");
  return {
    fecha,
    inicio: hora.slice(0, 5),
    canal: canalUi(cita.canal),
    estilo: estiloServicio(cita.tipo),
  };
}

/** Comprobante de una cita recién reservada: tarjeta teal con check animado y barrido de luz. */
export function CitaConfirmada({ cita, etiqueta = "Cita confirmada" }: { cita: Cita; etiqueta?: string }) {
  const { fecha, inicio, canal } = datosCita(cita);
  const IconoCanal = canal.icono;
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-co-teal to-co-teal-deep p-5 text-white shadow-lift animate-rise">
      <span className="sheen-barra pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 animate-sheen" aria-hidden="true" />
      <div className="flex items-start gap-4">
        <div className="relative flex h-12 w-12 shrink-0 items-center justify-center">
          <span className="halo-pulso absolute inset-0 rounded-full bg-co-sage animate-halo" aria-hidden="true" />
          <span className="relative flex h-12 w-12 items-center justify-center rounded-full bg-co-sage text-white animate-pop-in">
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12.5l4.5 4.5L19 7.5" strokeDasharray="26" className="animate-draw" />
            </svg>
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal-tint">{etiqueta}</p>
          <p className="mt-0.5 truncate text-lg font-extrabold leading-tight">{cita.servicio_nombre}</p>
          <p className="text-sm text-co-teal-tint">{cita.tipo_label}</p>
        </div>
        <span className="tabular shrink-0 rounded-md bg-white/15 px-2 py-1 text-xs font-bold">{cita.id}</span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-white/15 pt-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-co-teal-tint">
            <CalendarClock size={12} aria-hidden="true" /> Fecha
          </dt>
          <dd className="mt-0.5 font-bold">{primeraMayuscula(fechaConDia(fecha))}</dd>
        </div>
        <div>
          <dt className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-co-teal-tint">
            <Clock size={12} aria-hidden="true" /> Hora
          </dt>
          <dd className="tabular mt-0.5 font-bold">{rangoHoras(inicio, cita.hora_fin)}</dd>
        </div>
        <div className="col-span-2 sm:col-span-1">
          <dt className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-co-teal-tint">
            <IconoCanal size={12} aria-hidden="true" /> Canal
          </dt>
          <dd className="mt-0.5 flex items-center gap-1 font-bold">
            {canal.label}
            {cita.canal === "in_person" && (
              <span className="inline-flex items-center gap-0.5 font-semibold text-co-teal-tint">
                · <MapPin size={12} aria-hidden="true" /> {nombreDistrito(cita.distrito)}
              </span>
            )}
          </dd>
        </div>
      </dl>

      <Link
        href="/campus/citas"
        className="co-foco mt-4 inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-sm font-bold text-co-teal-deep transition hover:bg-co-bg"
      >
        Ver mis citas
        <ArrowRight size={14} aria-hidden="true" />
      </Link>
    </div>
  );
}

/** Aviso de una cita que se acaba de cancelar. */
export function CitaCancelada({ cita }: { cita: Cita }) {
  const { fecha, inicio } = datosCita(cita);
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-co-coral/30 bg-co-coral-tint p-4 animate-rise">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-co-coral text-white animate-pop-in">
        <X size={20} strokeWidth={3} aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-coral-ink">Cita cancelada</p>
        <p className="truncate text-sm font-bold text-co-navy">{cita.servicio_nombre}</p>
        <p className="tabular text-xs font-semibold text-co-ink">
          {primeraMayuscula(fechaConDia(fecha))} · {inicio} · {cita.id}
        </p>
      </div>
    </div>
  );
}
