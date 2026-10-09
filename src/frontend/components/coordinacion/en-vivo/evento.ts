import { AlertTriangle, BellRing, CalendarCheck, CalendarX, Hourglass, Layers, LucideIcon, PackageCheck, PackagePlus, Users } from "lucide-react";
import { bloqueFecha, distritoLabel, num, rangoHoras } from "@/lib/format";
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
  servicio_en_lote: {
    label: "Servicio en modo lote",
    corto: "En lote",
    icono: Layers,
    solido: "bg-co-coral",
    tinte: "bg-co-coral-tint",
    tinta: "text-co-coral-ink",
    borde: "border-co-coral",
  },
  servicio_sale_de_lote: {
    label: "Sale del modo lote",
    corto: "Directo",
    icono: Layers,
    solido: "bg-co-sage",
    tinte: "bg-co-sage-tint",
    tinta: "text-co-sage-ink",
    borde: "border-co-sage",
  },
  lote_abierto: {
    label: "Lote abierto",
    corto: "Lote",
    icono: PackagePlus,
    solido: "bg-co-teal",
    tinte: "bg-co-teal-tint",
    tinta: "text-co-teal-dark",
    borde: "border-co-teal",
  },
  lote_solicitud: {
    label: "Solicitud en lote",
    corto: "Lote",
    icono: Users,
    solido: "bg-co-teal",
    tinte: "bg-co-teal-tint",
    tinta: "text-co-teal-dark",
    borde: "border-co-teal",
  },
  lote_resuelto: {
    label: "Lote resuelto",
    corto: "Lote",
    icono: PackageCheck,
    solido: "bg-co-teal",
    tinte: "bg-co-teal-tint",
    tinta: "text-co-teal-dark",
    borde: "border-co-teal",
  },
  lista_espera_alta: {
    label: "En lista de espera",
    corto: "Espera",
    icono: Hourglass,
    solido: "bg-co-amber",
    tinte: "bg-co-amber-tint",
    tinta: "text-co-amber-ink",
    borde: "border-co-amber",
  },
  lista_espera_aviso: {
    label: "Aviso de cupo enviado",
    corto: "Aviso",
    icono: BellRing,
    solido: "bg-co-sage",
    tinte: "bg-co-sage-tint",
    tinta: "text-co-sage-ink",
    borde: "border-co-sage",
  },
};

export const ORIGEN_LABEL: Record<EventoActividad["origen"], string> = {
  chat: "AURA · chat",
  api: "API",
  lote: "Lote",
  sistema: "Sistema",
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
  if (e.espera) {
    return e.espera.cupo ? `Se le avisó de: ${e.espera.cupo}` : `${e.espera.motivo_label} · espera ${e.espera.franjas}`;
  }
  if (e.tipo === "servicio_en_lote" || e.tipo === "servicio_sale_de_lote") {
    const o = e.ocupacion;
    return o ? `Ocupación ${num(o.pct)} % · umbral ${num(e.umbral_pct ?? 0)} %` : "";
  }
  if (e.lote) {
    const l = e.lote;
    const r = l.resultado;
    if (r) {
      return r.error
        ? `Error al asignar: ${r.error}`
        : `${r.asignados} asignadas · ${r.sin_cupo} sin cupo${r.espera_media != null ? ` · espera media ${num(r.espera_media)} d` : ""}`;
    }
    return `${l.solicitudes} de ${l.tamano_maximo} solicitudes · se cierra solo`;
  }
  return "";
}

export function lugarEvento(e: EventoActividad): string {
  if (e.servicio) return `${e.servicio.nombre} · ${distritoLabel(e.servicio.distrito)}`;
  if (e.desencuentro) return `${e.desencuentro.servicio_ideal_label} · ${distritoLabel(e.desencuentro.distrito)}`;
  if (e.espera) return `${e.espera.servicio_ideal_label} · ${distritoLabel(e.espera.distrito)}`;
  if (e.lote) return `Lote ${e.lote.id}`;
  return "";
}

/** Hora local del registro (HH:MM:SS). */
export function horaRegistro(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
