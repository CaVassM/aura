"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { CalendarRange, Info, Share2 } from "lucide-react";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { rangoCorto } from "@/lib/format";
import { RUTA_EN_VIVO, useActividad } from "./ActividadProvider";
import { useDemo } from "./DemoProvider";
import { coordinacionNav } from "./nav";
import AvisosActividad from "./en-vivo/AvisosActividad";
import ReiniciarDemo from "./ReiniciarDemo";

/**
 * Marco de las pantallas de Coordinación: barra lateral en teal profundo y cabecera con el
 * escenario y un chip con la agenda abierta. Vive en el layout, así que solo el contenido se
 * recarga (con fundido) al cambiar de sección.
 */
export default function CoordinacionShell({ children }: { children: ReactNode }) {
  const ruta = usePathname();
  const { estado, error, cargando, reintentar } = useDemo();
  const { sinVer, conectado, loteAbierto } = useActividad();

  return (
    <div className="flex min-h-screen bg-co-bg text-co-navy">
      <AvisosActividad />
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col overflow-y-auto bg-co-teal-deep px-4 py-6 text-co-bg lg:flex">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-co-bg text-co-teal-deep">
            <Share2 size={18} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-extrabold leading-tight">Red de Bienestar</p>
            <p className="truncate text-xs leading-tight text-co-bg/80">Aethera · Coordinación</p>
          </div>
        </div>

        <nav className="mt-8 flex flex-col gap-1" aria-label="Coordinación">
          {coordinacionNav.map((item) => {
            const activo = ruta === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={activo ? "page" : undefined}
                className={`co-foco relative flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold transition-colors ${
                  activo
                    ? "bg-white/10 text-white"
                    : "text-co-bg/80 hover:bg-white/5 hover:text-white"
                }`}
              >
                {activo && (
                  <span className="absolute inset-y-2 left-0 w-1 rounded-r bg-co-amber" aria-hidden="true" />
                )}
                <span className="shrink-0 [&>svg]:h-[18px] [&>svg]:w-[18px]">{item.icon}</span>
                {item.label}
                {item.href === "/coordinacion/lotes" && loteAbierto && (
                  <span
                    className="ml-auto h-2 w-2 animate-breathe rounded-full bg-co-amber"
                    title="Hay un lote abierto"
                    aria-label="Hay un lote abierto"
                  />
                )}
                {item.href === RUTA_EN_VIVO && (
                  <span className="ml-auto flex items-center gap-1.5">
                    {sinVer > 0 && (
                      <span className="tabular rounded-full bg-co-coral px-1.5 py-0.5 text-[11px] font-extrabold leading-none text-white animate-pop-in">
                        {sinVer}
                      </span>
                    )}
                    <span
                      className={`h-2 w-2 rounded-full ${conectado ? "bg-co-sage animate-breathe" : "bg-co-amber"}`}
                      title={conectado ? "Conectado en tiempo real" : "Reconectando…"}
                      aria-hidden="true"
                    />
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-4 pt-6">
          <p className="flex items-start gap-2 text-xs leading-relaxed text-co-bg/80">
            <Info size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
            AURA solo asigna sobre cupos liberados. Este panel no permite asignaciones manuales.
          </p>
          <Link href="/" className="co-foco block text-xs font-semibold text-co-bg/80 hover:text-white">
            ← Volver a AURA
          </Link>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col lg:pl-60">
        <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-co-line px-6 py-4 lg:px-10">
          <div className="min-w-0">
            <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">
              Coordinación
            </p>
            <p className="text-sm font-semibold leading-snug text-co-navy">
              {estado ? estado.etiqueta : "Conectando con el backend…"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {estado && (
              <span className="inline-flex items-center gap-2 rounded-md bg-co-teal-tint px-3 py-1.5 text-sm font-bold text-co-teal-dark">
                <CalendarRange size={15} aria-hidden="true" />
                Agenda abierta · {rangoCorto(estado.agenda_abierta_inicio, estado.agenda_abierta_fin)} (
                {estado.agenda_abierta_semanas} semanas)
              </span>
            )}
            {estado && <ReiniciarDemo />}
          </div>
        </header>

        {/* Navegación compacta cuando no cabe la barra lateral */}
        <nav className="flex gap-1 overflow-x-auto border-b border-co-line px-4 py-2 lg:hidden" aria-label="Coordinación">
          {coordinacionNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`co-foco whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-semibold ${
                ruta === item.href ? "bg-co-teal text-white" : "text-co-ink"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <main className="flex-1 px-6 py-8 lg:px-10">
          {error ? (
            <EstadoError error={error} onRetry={reintentar} />
          ) : cargando && !estado ? (
            <EstadoCarga texto="Conectando con el backend…" />
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  );
}
