"use client";

import { useEffect, useState } from "react";
import { Info, Sparkles } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { coordinacionBrand, coordinacionNav } from "@/components/coordinacion/nav";
import StatCard from "@/components/ui/StatCard";
import { getNetworkSummary } from "@/lib/api";
import { NetworkSummary } from "@/lib/types";

function levelOf(pct: number): "green" | "yellow" | "red" {
  if (pct > 70) return "red";
  if (pct >= 50) return "yellow";
  return "green";
}
const BAR_COLOR = {
  green: "bg-aura-chart-green",
  yellow: "bg-aura-chart-yellow",
  red: "bg-aura-chart-red",
} as const;

export default function CoordinacionResumenPage() {
  const [summary, setSummary] = useState<NetworkSummary | null>(null);

  useEffect(() => {
    getNetworkSummary().then(setSummary);
  }, []);

  return (
    <PortalShell
      brandIcon={coordinacionBrand.icon}
      brandIconBg={coordinacionBrand.iconBg}
      brandName={coordinacionBrand.name}
      brandSubtitle={coordinacionBrand.subtitle}
      nav={coordinacionNav}
      activeHref="/coordinacion"
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
      subtitle="Semana del 5 al 10 de octubre de 2026 · Datos sintéticos"
      topbarRight={
        <span className="flex items-center gap-1.5 text-base font-extrabold text-aura-navy">
          <Sparkles size={16} className="text-aura-teal" />
          AURA
        </span>
      }
    >
      <div className="mx-auto max-w-5xl space-y-6 px-8 py-8">
        <div>
          <p className="text-xs font-bold tracking-wide text-aura-teal">
            RESUMEN DE RED
          </p>
          <h2 className="mt-1.5 text-3xl font-bold text-aura-navy">
            Cupos liberados, vistos con claridad.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-aura-gray">
            AURA propone y reserva automáticamente según disponibilidad. Este
            espacio observa la red, sin asignar cupos manualmente.
          </p>
        </div>

        {summary && (
          <>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StatCard
                label="Citas agendadas esta semana"
                value={String(summary.citasAgendadas)}
                tagText="Sobre cupos liberados"
                tagVariant="green"
              />
              <StatCard
                label="Espera media"
                value={`${summary.esperaMediaDias} días`}
                tagText={`Antes: ${summary.esperaMediaAntes} días`}
                tagVariant="purple"
              />
              <StatCard
                label="Ocupación de cupos liberados (%)"
                value={`${summary.ocupacionPct}%`}
                tagText={`${summary.cuposLiberados} cupos liberados`}
                tagVariant="yellow"
              />
              <StatCard
                label="Desencuentros registrados"
                value={String(summary.desencuentros)}
                tagText="Disponibilidad no compatible"
                tagVariant="red"
              />
            </div>

            <div className="rounded-xl2 border border-aura-border bg-white p-6 shadow-card">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-base font-bold text-aura-navy">
                    Ocupación de cupos liberados
                  </p>
                  <p className="text-sm text-aura-gray">
                    Por servicio · semana del 5 al 10 de octubre
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs text-aura-gray">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-aura-chart-green" />
                    Baja &lt; 50%
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-aura-chart-yellow" />
                    Media 50–70%
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-aura-chart-red" />
                    Alta &gt; 70%
                  </span>
                </div>
              </div>

              <div className="mt-6 space-y-3 border-t border-aura-border pt-5">
                {summary.servicios.map((s) => {
                  const level = levelOf(s.ocupacionPct);
                  return (
                    <div
                      key={s.nombre}
                      className="flex items-center gap-4 text-sm"
                    >
                      <span className="w-40 shrink-0 text-right text-aura-navy">
                        {s.nombre}
                      </span>
                      <div className="h-3 flex-1 overflow-hidden rounded-full bg-aura-bg">
                        <div
                          className={`h-full rounded-full ${BAR_COLOR[level]}`}
                          style={{ width: `${s.ocupacionPct}%` }}
                        />
                      </div>
                      <span className="w-10 shrink-0 text-xs text-aura-gray">
                        {s.ocupacionPct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </PortalShell>
  );
}
