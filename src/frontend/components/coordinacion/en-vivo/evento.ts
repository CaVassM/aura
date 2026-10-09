import { AlertTriangle, CalendarCheck, CalendarX, LucideIcon } from "lucide-react";
import { bloqueFecha, distritoLabel, rangoHoras } from "@/lib/format";
import { EventoActividad, TipoEvento } from "@/lib/types-coordinacion";

/** Cómo se ve cada tipo de evento (clases completas para que Tailwind las incluya). */
export const META_EVENTO: Record<
  TipoEvento,
  { label: string; corto: string; icono: LucideIcon; solido: string; tinte: string; tinta: string; borde: string }
> = {
  cita_reservada: {
    label: "Nueva cita",
    corto: "Reservada",
    icono: CalendarCheck,
    solido: "bg-co-sage",
    tinte: "bg-co-sage-tint",
    tinta: "text-co-sage-ink",
    borde: "border-co-sage",
  },
  cita_cancelada: {
    label: "Cita cancelada",
    corto: "Cancelada",
    icono: CalendarX,
    solido: "bg-co-coral",
    tinte: "bg-co-coral-tint",
    tinta: "text-co-coral-ink",
    borde: "border-co-coral",
  },
  desencuentro: {
    label: "Desencuentro",
    corto: "Sin cupo",
    icono: AlertTriangle,
    solido: "bg-co-amber",
    tinte: "bg-co-amber-tint",
    tinta: "text-co-amber-ink",
    borde: "border-co-amber",
  },
};

export const ORIGEN_LABEL: Record<EventoActividad["origen"], string> = {
  chat: "AURA · chat",
  api: "API",
};

/** "mié 25 nov · 10:00 – 11:00 · Videollamada" (citas) o lo que pedía la persona (desencuentros). */
export function detalleEvento(e: EventoActividad): string {
  if (e.cita) {
    const f = bloqueFecha(e.cita.fecha);
    return `${f.dia} ${f.numero} ${f.mes} · ${rangoHoras(e.cita.hora_inicio, e.cita.hora_fin)} · ${e.cita.canal_label}`;
  }
  if (e.desencuentro) {
    const d = e.desencuentro;
    return `${d.motivo_label} · pedía ${d.franjas}`;
  }
  return "";
}

export function lugarEvento(e: EventoActividad): string {
  if (e.servicio) return `${e.servicio.nombre} · ${distritoLabel(e.servicio.distrito)}`;
  if (e.desencuentro) return `${e.desencuentro.servicio_ideal_label} · ${distritoLabel(e.desencuentro.distrito)}`;
  return "";
}

/** Hora local del registro (HH:MM:SS). */
export function horaRegistro(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
