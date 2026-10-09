"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { RUTA_EN_VIVO, useActividad } from "../ActividadProvider";
import { detalleEvento, lugarEvento, META_EVENTO, ORIGEN_LABEL } from "./evento";

/**
 * Avisos emergentes (arriba a la derecha) cuando un estudiante agenda, cancela o no encuentra cupo.
 * Aparecen en cualquier pantalla de Coordinación y se van solos.
 */
export default function AvisosActividad() {
  const { avisos, cerrarAviso } = useActividad();
  if (!avisos.length) return null;

  return (
    <div
      className="pointer-events-none fixed right-4 top-4 z-[60] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2.5"
      role="status"
      aria-live="polite"
    >
      {avisos.map((e) => {
        const m = META_EVENTO[e.tipo];
        const Icono = m.icono;
        return (
          <div
            key={e.id}
            className={`pointer-events-auto relative flex items-start gap-3 overflow-hidden rounded-xl border bg-co-paper py-3 pl-4 pr-3 shadow-pop animate-slide-in-right ${m.borde}`}
          >
            <span className={`absolute inset-y-0 left-0 w-1.5 ${m.solido}`} aria-hidden="true" />
            <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${m.tinte} ${m.tinta}`}>
              <Icono size={16} aria-hidden="true" />
            </span>
            <Link href={RUTA_EN_VIVO} className="co-foco min-w-0 flex-1 rounded">
              <p className={`text-[11px] font-extrabold uppercase tracking-[0.14em] ${m.tinta}`}>{m.label}</p>
              <p className="truncate text-sm font-bold text-co-navy">{lugarEvento(e)}</p>
              <p className="truncate text-xs font-semibold text-co-ink">{detalleEvento(e)}</p>
              <p className="mt-0.5 text-[11px] font-semibold text-co-ink/80">
                {e.estudiante_id} · {ORIGEN_LABEL[e.origen]}
              </p>
            </Link>
            <button
              onClick={() => cerrarAviso(e.id)}
              aria-label="Cerrar aviso"
              className="co-foco rounded p-1 text-co-ink/70 transition hover:bg-co-bg hover:text-co-navy"
            >
              <X size={14} aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
