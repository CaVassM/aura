"use client";

import { Kpis } from "@/lib/types-coordinacion";
import { num } from "@/lib/format";
import Barra from "../Barra";
import InfoTip from "../InfoTip";
import NumeroAnimado from "../NumeroAnimado";

/**
 * La espera como protagonista: «42 días → 4,5 días» y una barra antes / después.
 * Antes = media observada en D2; después = espera media de la simulación (misma definición).
 */
export default function EsperaHeroe({ kpis }: { kpis: Kpis }) {
  const antes = kpis.espera_linea_base_dias;
  const despues = kpis.espera_media_dias;
  const mejora = antes > 0 ? Math.round((1 - despues / antes) * 100) : 0;

  return (
    <div className="flex h-full flex-col justify-between rounded-lg bg-co-teal-deep p-6 text-co-bg">
      <div>
        <p className="flex items-center text-xs font-extrabold uppercase tracking-[0.14em] text-co-bg">
          Espera media
          <InfoTip termino="espera_media" claro />
        </p>
        <p className="mt-4 flex flex-wrap items-baseline gap-x-3 gap-y-1 font-extrabold leading-none">
          <span className="text-4xl text-co-bg/80 sm:text-5xl">
            <NumeroAnimado valor={antes} decimales={0} />
            <span className="ml-1.5 text-xl font-bold">días</span>
          </span>
          <span className="text-3xl text-co-amber" aria-hidden="true">
            →
          </span>
          <span className="text-5xl text-white sm:text-6xl">
            <NumeroAnimado valor={despues} decimales={1} />
            <span className="ml-1.5 text-xl font-bold">días</span>
          </span>
        </p>
        {mejora > 0 && (
          <p className="mt-3 text-sm font-semibold text-co-bg">
            <span className="font-extrabold text-co-amber">−{num(mejora, 0)} %</span> de espera
          </p>
        )}
      </div>

      <div className="mt-6 space-y-3 text-xs font-semibold text-co-bg">
        <div>
          <div className="mb-1 flex justify-between">
            <span>Antes · observado en D2</span>
            <span className="tabular">{num(antes, 0)} d</span>
          </div>
          <Barra pct={100} color="bg-co-bg/45" pista="bg-white/10" alto="h-2.5" />
        </div>
        <div>
          <div className="mb-1 flex justify-between">
            <span>Con AURA · simulación</span>
            <span className="tabular">{num(despues, 1)} d</span>
          </div>
          <Barra
            pct={antes > 0 ? (despues / antes) * 100 : 0}
            color="bg-co-amber"
            pista="bg-white/10"
            alto="h-2.5"
            retraso={250}
          />
        </div>
      </div>
    </div>
  );
}
