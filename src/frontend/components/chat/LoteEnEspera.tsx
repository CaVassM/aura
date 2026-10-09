"use client";

import { useRef } from "react";
import { Check, Layers } from "lucide-react";
import { mmss, useCuentaRegresiva } from "@/components/coordinacion/lotes/useCuentaRegresiva";
import { LoteEstado } from "@/lib/types";

const RADIO = 26;
const CIRCUNFERENCIA = 2 * Math.PI * RADIO;

/** La persona está esperando en un lote: cuenta regresiva en anillo hasta que se cierre solo y asigne. */
export default function LoteEnEspera({ lote, resuelto }: { lote: LoteEstado; resuelto: boolean }) {
  const restante = useCuentaRegresiva(resuelto ? null : lote.cierra_en, undefined) ?? 0;
  const maximo = useRef(0);
  maximo.current = Math.max(maximo.current, restante);
  const avance = resuelto ? 0 : maximo.current > 0 ? restante / maximo.current : 0;
  const asignando = !resuelto && restante <= 0;

  return (
    <div
      className={`flex items-center gap-4 rounded-2xl border p-4 shadow-card animate-rise ${
        resuelto ? "border-co-line bg-white opacity-70" : "border-co-teal/40 bg-co-teal-tint/60"
      }`}
    >
      <div className="relative h-16 w-16 shrink-0">
        <svg viewBox="0 0 64 64" className="h-16 w-16 -rotate-90" aria-hidden="true">
          <circle cx="32" cy="32" r={RADIO} fill="none" strokeWidth="6" className="stroke-co-line" />
          <circle
            cx="32"
            cy="32"
            r={RADIO}
            fill="none"
            strokeWidth="6"
            strokeLinecap="round"
            className={resuelto ? "stroke-co-sage" : "stroke-co-teal"}
            strokeDasharray={CIRCUNFERENCIA}
            strokeDashoffset={CIRCUNFERENCIA * (resuelto ? 0 : 1 - avance)}
            style={{ transition: "stroke-dashoffset 300ms linear" }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-extrabold text-co-navy tabular">
          {resuelto ? <Check size={20} className="text-co-sage-ink" aria-hidden="true" /> : asignando ? <Layers size={18} className="animate-breathe" aria-hidden="true" /> : mmss(restante)}
        </span>
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal-dark">
          {resuelto ? "Lote resuelto" : `Lote ${lote.id} · en espera`}
        </p>
        <p className="text-sm font-bold text-co-navy">
          {resuelto
            ? "Ya tienes tu resultado más abajo."
            : asignando
              ? "Asignando en conjunto…"
              : `Vas ${lote.posicion}º de ${lote.solicitudes} · se cierra solo`}
        </p>
        {!resuelto && (
          <p className="text-xs font-medium text-co-ink">
            Se cierra a los {mmss(maximo.current || restante)} o al juntar {lote.tamano_maximo} solicitudes. Te aviso aquí con tu cita.
          </p>
        )}
      </div>
    </div>
  );
}
