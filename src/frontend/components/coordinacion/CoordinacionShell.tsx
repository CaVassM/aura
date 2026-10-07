"use client";

import { ReactNode } from "react";
import { Info, Sparkles } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { coordinacionBrand, coordinacionNav } from "./nav";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { rangoFechas } from "@/lib/format";
import { useDemo } from "./DemoProvider";
import ReiniciarDemo from "./ReiniciarDemo";

/** Marco común de las pantallas de Coordinación: cabecera con el escenario y la agenda abierta. */
export default function CoordinacionShell({
  activeHref,
  children,
}: {
  activeHref: string;
  children: ReactNode;
}) {
  const { estado, error, cargando, reintentar } = useDemo();

  return (
    <PortalShell
      brandIcon={coordinacionBrand.icon}
      brandIconBg={coordinacionBrand.iconBg}
      brandName={coordinacionBrand.name}
      brandSubtitle={coordinacionBrand.subtitle}
      nav={coordinacionNav}
      activeHref={activeHref}
      exitHref="/"
      exitLabel="Volver a AURA"
      sidebarFooter={
        <div className="flex items-start gap-2 rounded-xl bg-aura-teal-pale px-3 py-3 text-xs leading-relaxed text-aura-gray">
          <Info size={14} className="mt-0.5 shrink-0 text-aura-teal" />
          AURA solo asigna sobre cupos liberados. Este panel no permite
          asignaciones manuales.
        </div>
      }
      title="Red de Bienestar Aethera · Coordinación"
      subtitle={
        estado ? (
          <>
            <span className="block font-medium text-aura-navy">
              {estado.etiqueta}
            </span>
            <span className="block">
              Agenda abierta:{" "}
              {rangoFechas(
                estado.agenda_abierta_inicio,
                estado.agenda_abierta_fin,
              )}
            </span>
          </>
        ) : (
          "Conectando con el backend…"
        )
      }
      topbarRight={
        <>
          {estado && <ReiniciarDemo />}
          <span className="flex items-center gap-1.5 text-base font-extrabold text-aura-navy">
            <Sparkles size={16} className="text-aura-teal" />
            AURA
          </span>
        </>
      }
    >
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : cargando && !estado ? (
        <EstadoCarga texto="Conectando con el backend…" />
      ) : (
        children
      )}
    </PortalShell>
  );
}
