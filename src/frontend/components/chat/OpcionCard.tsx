import { ArrowRight, Check, Clock, Layers, MapPin } from "lucide-react";
import { bloqueFecha, rangoHoras } from "@/lib/format";
import { nombreDistrito } from "@/lib/perfiles";
import { canalUi, estiloServicio } from "@/lib/servicios-ui";
import { esLote, Opcion } from "@/lib/types";

interface Props {
  opcion: Opcion;
  numero: number;
  /** false cuando la opción ya no se puede elegir (hay una lista más nueva o ya se reservó). */
  activa: boolean;
  elegida: boolean;
  onElegir: (opcion: Opcion, numero: number) => void;
  indice: number;
}

/**
 * Una opción de cita propuesta por el agente. Al tocarla se le responde «quiero la opción N» al
 * agente, que es quien reserva: la tarjeta no reserva por sí sola.
 */
export default function OpcionCard({ opcion, numero, activa, elegida, onElegir, indice }: Props) {
  if (esLote(opcion)) return <OpcionLoteCard opcion={opcion} numero={numero} activa={activa} elegida={elegida} onElegir={onElegir} indice={indice} />;
  const estilo = estiloServicio(opcion.tipo);
  const Icono = estilo.icono;
  const canal = canalUi(opcion.canal);
  const IconoCanal = canal.icono;
  const f = bloqueFecha(opcion.fecha);

  return (
    <button
      type="button"
      disabled={!activa}
      onClick={() => onElegir(opcion, numero)}
      aria-label={`Opción ${numero}: ${opcion.servicio_nombre}, ${f.dia} ${f.numero} ${f.mes}, ${rangoHoras(opcion.hora_inicio, opcion.hora_fin)}, ${canal.label}`}
      style={{ animationDelay: `${indice * 90}ms` }}
      className={`co-foco group relative w-full overflow-hidden rounded-2xl border bg-white text-left shadow-card animate-rise transition duration-300 ${
        elegida ? "border-co-teal ring-2 ring-co-teal/30" : "border-co-line"
      } ${
        activa
          ? `hover:-translate-y-0.5 hover:shadow-lift ${estilo.borde}`
          : "cursor-default opacity-55 saturate-50"
      }`}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${estilo.solido}`} aria-hidden="true" />
      <div className="flex items-stretch gap-3 py-4 pl-4 pr-3 sm:gap-4 sm:pl-5 sm:pr-4">
        {/* Bloque de calendario */}
        <div className={`flex w-14 shrink-0 flex-col items-center justify-center rounded-xl py-2 sm:w-16 ${estilo.tinte} ${estilo.tinta}`}>
          <span className="text-[10px] font-extrabold uppercase tracking-[0.14em]">{f.dia}</span>
          <span className="tabular text-2xl font-extrabold leading-none">{f.numero}</span>
          <span className="text-[10px] font-bold uppercase tracking-wider">{f.mes}</span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${estilo.tinte} ${estilo.tinta}`}>
              <Icono size={12} aria-hidden="true" />
              {opcion.tipo_label}
            </span>
            {opcion.es_alternativa && (
              <span className="rounded-md bg-co-amber-tint px-2 py-0.5 text-[11px] font-bold text-co-amber-ink">
                Servicio alternativo
              </span>
            )}
          </div>
          <p className="mt-1.5 line-clamp-2 text-[15px] font-extrabold leading-snug text-co-navy">{opcion.servicio_nombre}</p>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-co-ink">
            <span className="tabular inline-flex items-center gap-1">
              <Clock size={13} aria-hidden="true" />
              {rangoHoras(opcion.hora_inicio, opcion.hora_fin)}
            </span>
            <span className="inline-flex items-center gap-1">
              <IconoCanal size={13} aria-hidden="true" />
              {canal.label}
            </span>
            {opcion.canal === "in_person" && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={13} aria-hidden="true" />
                {nombreDistrito(opcion.distrito)}
              </span>
            )}
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end justify-between">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-extrabold ${
              elegida ? "bg-co-teal text-white" : "bg-co-bg text-co-ink"
            }`}
            aria-hidden="true"
          >
            {elegida ? <Check size={13} /> : numero}
          </span>
          {activa && (
            <span className="flex items-center gap-1 text-xs font-bold text-co-teal opacity-0 transition duration-300 group-hover:translate-x-0.5 group-hover:opacity-100">
              Elegir
              <ArrowRight size={14} aria-hidden="true" />
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

/**
 * Un servicio con mucha demanda (modo lote): sus cupos se reparten en grupo, así que no hay día ni hora para elegir. Al
 * tocarla la solicitud queda pendiente y el resultado llega al mismo chat en unos segundos.
 */
function OpcionLoteCard({ opcion, numero, activa, elegida, onElegir, indice }: Props) {
  const estilo = estiloServicio(opcion.tipo);
  const Icono = estilo.icono;
  return (
    <button
      type="button"
      disabled={!activa}
      onClick={() => onElegir(opcion, numero)}
      aria-label={`Opción ${numero}: ${opcion.servicio_nombre}, asignación en grupo. ${opcion.mensaje ?? ""}`}
      style={{ animationDelay: `${indice * 90}ms` }}
      className={`co-foco group relative w-full overflow-hidden rounded-2xl border bg-gradient-to-br from-co-amber-tint to-co-paper text-left shadow-card animate-rise transition duration-300 ${
        elegida ? "border-co-amber ring-2 ring-co-amber/30" : "border-co-amber/50"
      } ${activa ? "hover:-translate-y-0.5 hover:shadow-lift" : "cursor-default opacity-55 saturate-50"}`}
    >
      <span className="absolute inset-y-0 left-0 w-1.5 bg-co-amber" aria-hidden="true" />
      <div className="flex items-stretch gap-3 py-4 pl-4 pr-3 sm:gap-4 sm:pl-5 sm:pr-4">
        <div className="flex w-14 shrink-0 flex-col items-center justify-center rounded-xl bg-co-amber py-2 text-white sm:w-16">
          <Layers size={22} aria-hidden="true" />
          <span className="mt-1 text-center text-[9px] font-extrabold uppercase leading-tight tracking-[0.1em]">En grupo</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${estilo.tinte} ${estilo.tinta}`}>
              <Icono size={12} aria-hidden="true" />
              {opcion.tipo_label}
            </span>
            <span className="rounded-md bg-co-amber px-2 py-0.5 text-[11px] font-extrabold text-white">Asignación en grupo</span>
            {opcion.es_alternativa && (
              <span className="rounded-md bg-co-amber-tint px-2 py-0.5 text-[11px] font-bold text-co-amber-ink">Servicio alternativo</span>
            )}
          </div>
          <p className="mt-1.5 line-clamp-2 text-[15px] font-extrabold leading-snug text-co-navy">{opcion.servicio_nombre}</p>
          <p className="mt-1 text-xs font-semibold leading-relaxed text-co-ink">
            {opcion.mensaje ?? "Este servicio tiene mucha demanda; sus cupos se reparten en grupo."}
          </p>
          <p className="tabular mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-bold text-co-amber-ink">
            {opcion.cupos_libres != null && <span>{opcion.cupos_libres} cupos libres</span>}
            {opcion.tiempo_respuesta_s != null && (
              <span className="inline-flex items-center gap-1">
                <Clock size={13} aria-hidden="true" />
                respuesta en ~{opcion.tiempo_respuesta_s} s
              </span>
            )}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end justify-between">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-extrabold ${
              elegida ? "bg-co-amber text-white" : "bg-co-bg text-co-ink"
            }`}
            aria-hidden="true"
          >
            {elegida ? <Check size={13} /> : numero}
          </span>
          {activa && (
            <span className="flex items-center gap-1 text-xs font-bold text-co-amber-ink opacity-0 transition duration-300 group-hover:translate-x-0.5 group-hover:opacity-100">
              Elegir
              <ArrowRight size={14} aria-hidden="true" />
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
