"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CalendarClock, Clock, MapPin, MessageCircle, Sparkles } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { usePerfil } from "@/components/campus/PerfilProvider";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav } from "@/components/campus/nav";
import { EstadoError } from "@/components/ui/Estados";
import { cancelarCita, getMisCitas } from "@/lib/api";
import { bloqueFecha, fechaConDia, primeraMayuscula, rangoHoras } from "@/lib/format";
import { nombreDistrito } from "@/lib/perfiles";
import { canalUi, estiloServicio } from "@/lib/servicios-ui";
import { Cita } from "@/lib/types";

function TarjetaCita({
  cita,
  indice,
  onCancelada,
}: {
  cita: Cita;
  indice: number;
  onCancelada: (c: Cita) => void;
}) {
  const [confirmando, setConfirmando] = useState(false);
  const [cancelando, setCancelando] = useState(false);
  const [fallo, setFallo] = useState(false);
  const [fecha, hora] = cita.slot.fecha_iso.split("T");
  const f = bloqueFecha(fecha);
  const estilo = estiloServicio(cita.tipo);
  const Icono = estilo.icono;
  const canal = canalUi(cita.canal);
  const IconoCanal = canal.icono;
  const activa = cita.estado === "confirmada";

  const cancelar = async () => {
    setCancelando(true);
    setFallo(false);
    try {
      onCancelada(await cancelarCita(cita.id, cita.estudiante_id));
    } catch {
      setFallo(true);
      setCancelando(false);
    }
  };

  return (
    <article
      style={{ animationDelay: `${indice * 80}ms` }}
      className={`relative overflow-hidden rounded-2xl border border-co-line bg-white shadow-card animate-rise transition duration-300 ${
        activa ? "hover:-translate-y-0.5 hover:shadow-lift" : "opacity-70"
      }`}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${activa ? estilo.solido : "bg-co-line"}`} aria-hidden="true" />
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 py-5 pl-6 pr-5">
        <div className={`flex w-[4.5rem] shrink-0 flex-col items-center rounded-xl py-2.5 ${activa ? `${estilo.tinte} ${estilo.tinta}` : "bg-co-bg text-co-ink"}`}>
          <span className="text-[10px] font-extrabold uppercase tracking-[0.14em]">{f.dia}</span>
          <span className="tabular text-3xl font-extrabold leading-none">{f.numero}</span>
          <span className="text-[10px] font-bold uppercase tracking-wider">{f.mes}</span>
        </div>

        <div className="min-w-0 flex-1 basis-56">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${estilo.tinte} ${estilo.tinta}`}>
              <Icono size={12} aria-hidden="true" />
              {cita.tipo_label}
            </span>
            <span
              className={`rounded-md px-2 py-0.5 text-[11px] font-bold ${
                activa ? "bg-co-sage-tint text-co-sage-ink" : "bg-co-coral-tint text-co-coral-ink"
              }`}
            >
              {activa ? "Confirmada" : "Cancelada"}
            </span>
          </div>
          <p className="mt-1.5 truncate text-base font-extrabold text-co-navy">{cita.servicio_nombre}</p>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-co-ink">
            <span>{primeraMayuscula(fechaConDia(fecha))}</span>
            <span className="tabular inline-flex items-center gap-1">
              <Clock size={13} aria-hidden="true" />
              {rangoHoras(hora.slice(0, 5), cita.hora_fin)}
            </span>
            <span className="inline-flex items-center gap-1">
              <IconoCanal size={13} aria-hidden="true" />
              {canal.label}
            </span>
            {cita.canal === "in_person" && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={13} aria-hidden="true" />
                {nombreDistrito(cita.distrito)}
              </span>
            )}
          </p>
          <p className="tabular mt-1 text-[11px] font-semibold text-co-ink/70">{cita.id}</p>
        </div>

        {activa && (
          <div className="flex shrink-0 items-center gap-2">
            {!confirmando ? (
              <button
                onClick={() => setConfirmando(true)}
                className="co-foco rounded-full border border-co-line px-4 py-2 text-sm font-bold text-co-ink transition hover:border-co-coral hover:bg-co-coral-tint hover:text-co-coral-ink"
              >
                Cancelar cita
              </button>
            ) : (
              <div className="flex items-center gap-2 animate-fade-only">
                <span className="text-xs font-bold text-co-navy">¿Cancelar?</span>
                <button
                  onClick={cancelar}
                  disabled={cancelando}
                  className="co-foco rounded-full bg-co-coral px-4 py-2 text-sm font-bold text-white transition hover:bg-co-coral-ink disabled:opacity-60"
                >
                  {cancelando ? "Cancelando…" : "Sí, cancelar"}
                </button>
                <button
                  onClick={() => setConfirmando(false)}
                  disabled={cancelando}
                  className="co-foco rounded-full px-3 py-2 text-sm font-bold text-co-ink hover:bg-co-bg"
                >
                  No
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      {fallo && (
        <p role="alert" className="border-t border-co-coral/30 bg-co-coral-tint px-6 py-2 text-xs font-bold text-co-coral-ink">
          No se pudo cancelar la cita. Inténtalo de nuevo.
        </p>
      )}
    </article>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="h-[116px] animate-pulse rounded-2xl border border-co-line bg-white/70" />
      ))}
    </div>
  );
}

export default function MisCitasPage() {
  const { perfil } = usePerfil();
  const [citas, setCitas] = useState<Cita[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  const cargar = useCallback(() => {
    setCitas(null);
    setError(null);
    getMisCitas(perfil.id).then(setCitas).catch(setError);
  }, [perfil.id]);

  useEffect(cargar, [cargar]);

  const alCancelar = (cancelada: Cita) =>
    setCitas((lista) => lista?.map((c) => (c.id === cancelada.id ? cancelada : c)) ?? null);

  const confirmadas = citas?.filter((c) => c.estado === "confirmada").length ?? 0;

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/citas"
      exitHref="/"
      exitLabel="Salir del campus"
      title="Mis citas"
      subtitle={
        citas === null
          ? "Citas agendadas con servicios de bienestar"
          : `${confirmadas} ${confirmadas === 1 ? "cita confirmada" : "citas confirmadas"}`
      }
      topbarRight={<TopbarControls />}
    >
      <div className="chat-lienzo min-h-full px-4 py-8 lg:px-8">
        <div className="mx-auto max-w-3xl space-y-3">
          {error ? (
            <EstadoError error={error} onRetry={cargar} />
          ) : citas === null ? (
            <Esqueleto />
          ) : citas.length === 0 ? (
            <div className="flex flex-col items-center gap-4 rounded-3xl border border-dashed border-co-line bg-white/70 px-8 py-20 text-center animate-rise">
              <span className="flex h-14 w-14 animate-breathe items-center justify-center rounded-full bg-co-teal-tint text-co-teal">
                <CalendarClock size={26} aria-hidden="true" />
              </span>
              <div>
                <p className="text-lg font-extrabold text-co-navy">Todavía no tienes citas, {perfil.corto}</p>
                <p className="mt-1 text-sm text-co-ink">Cuéntale a AURA qué necesitas y encontrará un horario para ti.</p>
              </div>
              <Link
                href="/campus/chat"
                className="co-foco flex items-center gap-2 rounded-full bg-gradient-to-br from-co-teal to-co-teal-deep px-6 py-3 text-sm font-bold text-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lift"
              >
                <MessageCircle size={16} aria-hidden="true" />
                Hablar con AURA
              </Link>
            </div>
          ) : (
            <>
              {citas.map((c, i) => (
                <TarjetaCita key={c.id} cita={c} indice={i} onCancelada={alCancelar} />
              ))}
              <Link
                href="/campus/chat"
                className="co-foco mt-2 inline-flex items-center gap-2 rounded-full border border-co-line bg-white px-5 py-2.5 text-sm font-bold text-co-teal-dark shadow-card transition hover:border-co-teal hover:bg-co-teal-tint"
              >
                <Sparkles size={15} aria-hidden="true" />
                Agendar otra cita con AURA
              </Link>
            </>
          )}
        </div>
      </div>
    </PortalShell>
  );
}
