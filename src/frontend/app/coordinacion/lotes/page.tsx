"use client";

import { useState } from "react";
import { Layers } from "lucide-react";
import { useApi } from "@/components/coordinacion/useApi";
import Seccion from "@/components/coordinacion/Seccion";
import LoteAbierto from "@/components/coordinacion/lotes/LoteAbierto";
import ResultadoLote from "@/components/coordinacion/lotes/ResultadoLote";
import ServiciosUmbral from "@/components/coordinacion/lotes/ServiciosUmbral";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getLotes } from "@/lib/api";
import { num } from "@/lib/format";

export default function LotesPage() {
  // Se recarga sola: cada novedad del modo lote llega por el flujo en tiempo real (ver ActividadProvider).
  const { data, error, reintentar } = useApi(() => getLotes(), []);
  const [abiertoId, setAbiertoId] = useState<number | null>(null);

  if (error) return <EstadoError error={error} onRetry={reintentar} />;
  if (!data) return <EstadoCarga />;

  const enLote = data.servicios.filter((s) => s.en_lote).length;
  const visible = abiertoId ?? data.historial[0]?.id ?? null;

  return (
    <div className="mx-auto max-w-7xl space-y-10">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Lotes</h1>
        <p className="mt-1 max-w-3xl text-sm font-medium leading-relaxed text-co-ink">
          Cuando un servicio llega al <strong className="font-extrabold">{num(data.umbral_pct)} %</strong> de utilización (cupos
          reservados sobre cupos liberados), deja de ofrecer sus cupos uno a uno: las solicitudes que solo encuentran
          servicios así esperan en un <strong className="font-extrabold">lote</strong>. El lote se cierra solo a los{" "}
          {data.ventana_s} s de entrar la primera solicitud, o al juntar {data.tamano_maximo}, y el algoritmo genético
          reparte los cupos entre todas a la vez.
        </p>
      </div>

      <Seccion titulo="Lote abierto" acento="bg-co-teal">
        {data.abierto ? (
          <LoteAbierto lote={data.abierto} ventanaS={data.ventana_s} tamanoMaximo={data.tamano_maximo} servidorAhora={data.servidor_ahora} />
        ) : (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-co-line bg-co-paper px-8 py-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-co-teal-tint text-co-teal">
              <Layers size={22} aria-hidden="true" />
            </span>
            <p className="text-base font-extrabold text-co-navy">No hay un lote abierto</p>
            <p className="max-w-lg text-sm text-co-ink">
              Se abre cuando un estudiante pide una cita y todo lo compatible está en servicios en modo lote. Aparecerá
              aquí con su cuenta regresiva.
            </p>
          </div>
        )}
      </Seccion>

      <Seccion
        titulo="Servicios por utilización"
        acento="bg-co-coral"
        derecha={
          <p className="text-sm font-bold text-co-navy">
            <span className="text-co-coral-ink">{enLote}</span> de {data.servicios.length} en modo lote · la marca indica el{" "}
            {num(data.umbral_pct)} %
          </p>
        }
      >
        <ServiciosUmbral servicios={data.servicios} umbralPct={data.umbral_pct} />
      </Seccion>

      <Seccion titulo="Lotes resueltos" acento="bg-co-amber">
        {data.historial.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-co-line bg-co-paper px-6 py-8 text-center text-sm font-medium text-co-ink">
            Todavía no se resolvió ningún lote desde que arrancó la demo.
          </p>
        ) : (
          <div className="space-y-3">
            {data.historial.map((l) => {
              const abierto = visible === l.id;
              const r = l.resultado;
              return (
                <div key={l.id} className="overflow-hidden rounded-2xl border border-co-line bg-co-paper shadow-card">
                  <button
                    type="button"
                    onClick={() => setAbiertoId(abierto ? -1 : l.id)}
                    aria-expanded={abierto}
                    className="co-foco flex w-full flex-wrap items-center justify-between gap-3 px-5 py-4 text-left"
                  >
                    <span className="text-base font-extrabold text-co-navy">
                      Lote {l.id}
                      <span className="ml-2 text-sm font-semibold text-co-ink">
                        {l.cerrado_en && new Date(l.cerrado_en).toLocaleTimeString("es-ES")} · {l.solicitudes.length}{" "}
                        {l.solicitudes.length === 1 ? "solicitud" : "solicitudes"}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 text-xs font-bold">
                      {r && !r.error && (
                        <>
                          <span className="rounded bg-co-sage-tint px-2 py-1 text-co-sage-ink">{r.asignados} asignadas</span>
                          {r.sin_cupo > 0 && <span className="rounded bg-co-amber-tint px-2 py-1 text-co-amber-ink">{r.sin_cupo} sin cupo</span>}
                        </>
                      )}
                      <span className="text-co-ink">{abierto ? "Ocultar" : "Ver detalle"}</span>
                    </span>
                  </button>
                  {abierto && (
                    <div className="border-t border-co-line px-5 py-4 animate-fade-in">
                      <ResultadoLote lote={l} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Seccion>
    </div>
  );
}
