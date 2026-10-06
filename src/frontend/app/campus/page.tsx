"use client";

import { useState } from "react";
import Link from "next/link";
import { CalendarDays, Info, MessageCircle, Sparkles } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav, campusUser } from "@/components/campus/nav";

function todayLabel() {
  const s = new Date().toLocaleDateString("es-PE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function CampusInicioPage() {
  const [showPrompt, setShowPrompt] = useState(true);

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus"
      user={campusUser}
      exitHref="/"
      exitLabel="Salir del campus"
      title="Inicio"
      subtitle={todayLabel()}
      topbarRight={<TopbarControls />}
    >
      <div className="mx-auto max-w-3xl space-y-5 px-8 py-8">
        {/* Banner de calendario académico */}
        <div className="flex items-center justify-between gap-4 rounded-xl2 bg-aura-purple-pale px-6 py-5">
          <div>
            <p className="flex items-center gap-2 text-sm font-medium text-aura-purple">
              <CalendarDays size={16} />
              Calendario académico
            </p>
            <p className="mt-1 text-base font-bold text-aura-navy">
              Semana de evaluaciones parciales · 5-9 de octubre
            </p>
          </div>
          <Link
            href="/campus/calendario"
            className="shrink-0 rounded-full bg-white px-4 py-2 text-sm font-semibold text-aura-navy shadow-card"
          >
            4 evaluaciones programadas
          </Link>
        </div>

        {/* Tarjeta proactiva de AURA */}
        {showPrompt && (
          <div className="rounded-xl2 bg-aura-teal-pale px-7 py-7">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-aura-teal text-white">
              <Sparkles size={20} />
            </div>
            <p className="mt-4 text-2xl font-bold text-aura-navy">
              Un espacio para ti, cuando lo necesites.
            </p>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-aura-gray">
              En semanas de evaluaciones muchos estudiantes buscan apoyo.
              AURA te ayuda a encontrar una cita con los servicios de
              bienestar en pocos minutos, en el horario que te acomode.
            </p>

            <div className="mt-5 flex items-start gap-2 border-t border-aura-teal/15 pt-4 text-xs text-aura-gray">
              <Info size={14} className="mt-0.5 shrink-0" />
              Este aviso es opcional y aparece por el calendario académico.
              Puedes ocultarlo cuando quieras.
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Link
                href="/campus/chat"
                className="flex items-center gap-2 rounded-full bg-aura-teal px-5 py-2.5 text-sm font-semibold text-white hover:bg-aura-teal-dark"
              >
                <MessageCircle size={16} />
                Hablar con AURA
              </Link>
              <button
                onClick={() => setShowPrompt(false)}
                className="rounded-full border border-aura-border bg-white px-5 py-2.5 text-sm font-semibold text-aura-navy hover:bg-aura-bg"
              >
                Ahora no
              </button>
              <button
                onClick={() => setShowPrompt(false)}
                className="text-sm font-medium text-aura-gray hover:text-aura-navy"
              >
                No volver a mostrar este aviso
              </button>
            </div>
          </div>
        )}
      </div>
    </PortalShell>
  );
}
