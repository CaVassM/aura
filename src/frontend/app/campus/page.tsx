"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CalendarDays, Info, MessageCircle, Sparkles } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { usePerfil } from "@/components/campus/PerfilProvider";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav } from "@/components/campus/nav";
import { darDeBajaAviso, getAvisoProactivo, getDemoEstado } from "@/lib/api";
import { fechaConDia, fechaLarga } from "@/lib/format";
import { nombreDistrito } from "@/lib/perfiles";
import { SERVICIOS_UI } from "@/lib/servicios-ui";
import { AvisoProactivo } from "@/lib/types";
import { EstadoDemo } from "@/lib/types-coordinacion";

const SERVICIOS = [
  {
    tipo: "counseling",
    nombre: "Consejería",
    texto: "Conversación individual de acompañamiento por estrés, ánimo, sueño, concentración o presión académica.",
  },
  {
    tipo: "peer_support",
    nombre: "Apoyo entre pares",
    texto: "Conversar con otros estudiantes: apoyo social y compañía.",
  },
  {
    tipo: "career_guidance",
    nombre: "Orientación vocacional",
    texto: "Dudas sobre tu carrera y tu futuro profesional.",
  },
];

export default function CampusInicioPage() {
  const { perfil } = usePerfil();
  // El aviso solo aparece si la regla lo decide para esta persona (semana de evaluaciones + señales) y no lo dio de baja.
  const [aviso, setAviso] = useState<AvisoProactivo | null>(null);
  // La fecha es la de la demo (la simulación vive en el backend), no la del reloj del navegador.
  const [demo, setDemo] = useState<EstadoDemo | null>(null);

  useEffect(() => {
    getDemoEstado().then(setDemo).catch(() => setDemo(null));
  }, []);

  useEffect(() => {
    let vigente = true;
    setAviso(null);
    getAvisoProactivo(perfil.id)
      .then((a) => vigente && setAviso(a))
      .catch(() => vigente && setAviso(null));
    return () => {
      vigente = false;
    };
  }, [perfil.id]);

  const ocultarAviso = () => {
    setAviso((a) => (a ? { ...a, mostrar: false, descartado: true } : a));
    darDeBajaAviso(perfil.id).catch(() => undefined);
  };

  const subtitulo = demo ? fechaConDia(demo.hoy).replace(/^./, (c) => c.toUpperCase()) : `Hola, ${perfil.corto}`;

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus"
      exitHref="/"
      exitLabel="Salir del campus"
      title="Inicio"
      subtitle={subtitulo}
      topbarRight={<TopbarControls />}
    >
      <div className="chat-lienzo min-h-full px-4 py-8 lg:px-8">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="animate-rise">
            <p className="text-3xl font-extrabold tracking-tight text-co-navy">Hola, {perfil.corto}</p>
            <p className="mt-1 text-sm font-semibold text-co-ink">
              Tu distrito: {nombreDistrito(perfil.distrito)} · Universidad Nova
            </p>
          </div>

          {/* Calendario académico */}
          <div
            className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-co-amber/40 bg-co-amber-tint px-6 py-5 animate-rise"
            style={{ animationDelay: "80ms" }}
          >
            <div>
              <p className="flex items-center gap-2 text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-amber-ink">
                <CalendarDays size={14} aria-hidden="true" />
                Calendario académico
              </p>
              <p className="mt-1 text-base font-extrabold text-co-navy">
                Semana de evaluaciones
                {demo && ` · ${fechaLarga(demo.semana_inicio)} al ${fechaLarga(demo.semana_fin)}`}
              </p>
            </div>
            <Link
              href="/campus/calendario"
              className="co-foco flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-sm font-bold text-co-navy shadow-card transition hover:-translate-y-0.5 hover:shadow-lift"
            >
              Ver calendario
              <ArrowRight size={14} aria-hidden="true" />
            </Link>
          </div>

          {/* Tarjeta proactiva de AURA */}
          {aviso?.mostrar && (
            <div
              className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-co-teal to-co-teal-deep px-7 py-8 text-white shadow-lift animate-rise"
              style={{ animationDelay: "160ms" }}
            >
              <span className="pointer-events-none absolute -right-10 -top-10 h-44 w-44 rounded-full bg-white/10" aria-hidden="true" />
              <span className="pointer-events-none absolute -bottom-24 -right-10 h-48 w-48 rounded-full bg-co-coral/25" aria-hidden="true" />
              <span className="pointer-events-none absolute right-16 top-28 h-12 w-12 rounded-full bg-co-amber/30 animate-breathe" aria-hidden="true" />

              <div className="relative">
                <span className="inline-flex h-11 w-11 animate-breathe items-center justify-center rounded-xl bg-white text-co-teal-deep">
                  <Sparkles size={20} aria-hidden="true" />
                </span>
                <p className="mt-4 max-w-md text-3xl font-extrabold leading-tight tracking-tight">
                  Un espacio para ti, cuando lo necesites.
                </p>
                <p className="mt-2 max-w-xl text-sm leading-relaxed text-co-teal-tint">
                  En semanas de evaluaciones muchos estudiantes buscan apoyo. AURA te ayuda a encontrar una cita con los
                  servicios de bienestar en pocos minutos, en el horario que te acomode.
                </p>

                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <Link
                    href="/campus/chat"
                    className="co-foco flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-extrabold text-co-teal-deep shadow-card transition hover:-translate-y-0.5 hover:shadow-lift"
                  >
                    <MessageCircle size={16} aria-hidden="true" />
                    Hablar con AURA
                  </Link>
                  <button
                    onClick={ocultarAviso}
                    className="co-foco rounded-full border border-white/30 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10"
                  >
                    Ahora no
                  </button>
                </div>

                <p className="mt-5 flex items-start gap-2 border-t border-white/15 pt-4 text-xs text-co-teal-tint">
                  <Info size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
                  Este aviso es opcional y aparece por la semana de evaluaciones. Si pulsas «Ahora no», no te lo volveremos a mostrar.
                </p>
              </div>
            </div>
          )}

          {/* Servicios de la red */}
          <section aria-labelledby="servicios" className="animate-rise" style={{ animationDelay: "240ms" }}>
            <h2 id="servicios" className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">
              Servicios de la red
            </h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {SERVICIOS.map((s) => {
                const e = SERVICIOS_UI[s.tipo];
                const Icono = e.icono;
                return (
                  <div
                    key={s.tipo}
                    className="group relative overflow-hidden rounded-2xl border border-co-line bg-white p-4 shadow-card transition duration-300 hover:-translate-y-0.5 hover:shadow-lift"
                  >
                    <span className={`absolute inset-x-0 top-0 h-1 ${e.solido}`} aria-hidden="true" />
                    <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${e.tinte} ${e.tinta}`}>
                      <Icono size={18} aria-hidden="true" />
                    </span>
                    <p className="mt-3 text-sm font-extrabold text-co-navy">{s.nombre}</p>
                    <p className="mt-1 text-xs leading-relaxed text-co-ink">{s.texto}</p>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </PortalShell>
  );
}
