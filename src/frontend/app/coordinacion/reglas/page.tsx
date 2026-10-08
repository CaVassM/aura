"use client";

import { Info, LockKeyhole } from "lucide-react";
import Barra from "@/components/coordinacion/Barra";
import { useApi } from "@/components/coordinacion/useApi";
import ReglaCard from "@/components/coordinacion/reglas/ReglaCard";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getReglas } from "@/lib/api";
import { numFijo } from "@/lib/format";

export default function ReglasPage() {
  const { data: r, error, cargando, reintentar } = useApi(() => getReglas(), []);

  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Reglas del motor</h1>
        <span
          title="Se modifica en los archivos de configuración con aprobación de bienestar"
          className="inline-flex items-center gap-2 text-sm font-bold text-co-ink"
        >
          <LockKeyhole className="h-4 w-4" aria-hidden="true" />
          Solo lectura
        </span>
      </div>

      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !r ? (
        cargando && <EstadoCarga />
      ) : (
        <>
          <ReglaCard numero="01" titulo="Motivo → servicio" termino="regla_motivo" provisional={r.motivo_servicio.provisional}>
            <ul className="divide-y divide-co-line border-y border-co-line">
              {r.motivo_servicio.items.map((m) => (
                <li
                  key={m.motivo}
                  className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-3 text-sm"
                >
                  <span className="font-bold text-co-navy">{m.motivo_label}</span>
                  <span className="font-bold text-co-amber-ink" aria-hidden="true">→</span>
                  <span className="text-right font-extrabold text-co-teal">{m.servicio_label}</span>
                </li>
              ))}
            </ul>
          </ReglaCard>

          <ReglaCard numero="02" titulo="Afinidad" termino="regla_afinidad" provisional={r.afinidad.provisional}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[420px] border-separate border-spacing-1 text-center text-sm">
                <thead>
                  <tr>
                    <th className="p-2 text-left text-xs font-bold text-co-ink">Necesita ↓ · Servicio →</th>
                    {r.afinidad.tipos.map((t) => (
                      <th key={t.codigo} className="p-2 text-xs font-extrabold text-co-navy">
                        {t.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {r.afinidad.matriz.map((fila) => (
                    <tr key={fila.ideal}>
                      <th className="p-2 text-left text-sm font-extrabold text-co-navy">{fila.ideal_label}</th>
                      {fila.valores.map((v) => {
                        const propio = v.tipo === fila.ideal;
                        const alternativa = !propio && v.valor >= r.afinidad.minimo_alternativa;
                        return (
                          <td
                            key={v.tipo}
                            className={`tabular rounded-md p-3 text-base font-extrabold ${
                              propio
                                ? "bg-co-teal-tint text-co-teal-dark"
                                : alternativa
                                  ? "bg-co-sage-tint text-co-sage-ink"
                                  : "bg-co-line/40 text-co-ink"
                            }`}
                          >
                            {numFijo(v.valor, 1)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-sm font-medium text-co-ink">
              Mínimo para ofrecer alternativa:{" "}
              <strong className="tabular text-co-navy">{numFijo(r.afinidad.minimo_alternativa, 1)}</strong>
              {r.afinidad.minimo_provisional && " (provisional)"}. En verde, las alternativas permitidas.
            </p>
          </ReglaCard>

          <ReglaCard numero="03" titulo="Aviso académico" termino="regla_aviso" provisional={r.aviso.provisional}>
            <div className="grid gap-x-8 gap-y-4 md:grid-cols-2">
              {r.aviso.senales.map((s) => (
                <div key={s.id} className="flex gap-3 text-sm">
                  <span className="text-lg font-extrabold text-co-teal">{s.id}</span>
                  <span>
                    <span className="block font-extrabold text-co-navy">{s.nombre}</span>
                    <span className="block font-medium text-co-ink">{s.descripcion}</span>
                    <span className="mt-0.5 block text-xs font-bold text-co-navy">
                      Umbral: <span className="tabular">{s.umbral_texto}</span>
                    </span>
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-5 flex gap-2 border-l-4 border-co-teal bg-co-teal-tint px-4 py-3 text-sm font-medium text-co-navy">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-co-teal" aria-hidden="true" />
              <span>
                Se muestra aviso únicamente con {r.aviso.puntaje_minimo} o más señales
                {r.aviso.solo_semanas_evaluacion && " y solo durante semanas de evaluaciones"}. Estas
                señales nunca se muestran al estudiante.
              </span>
            </p>
          </ReglaCard>

          <div className="grid gap-10 md:grid-cols-2">
            <ReglaCard numero="04" titulo="Probabilidad de asistencia" termino="regla_asistencia" provisional={r.p_asistencia.provisional}>
              <ul className="space-y-3">
                {r.p_asistencia.canales.map((c, i) => (
                  <li key={c.canal} className="text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-bold text-co-navy">{c.canal_label}</span>
                      <span className="tabular font-extrabold text-co-teal">{numFijo(c.valor, 3)}</span>
                    </div>
                    <Barra pct={c.valor * 100} color="bg-co-teal" retraso={i * 80} />
                  </li>
                ))}
              </ul>
            </ReglaCard>

            <ReglaCard numero="05" titulo="Pesos del motor" termino="regla_pesos" provisional={r.pesos.provisional}>
              <ul className="space-y-3">
                {r.pesos.terminos.map((t, i) => (
                  <li key={t.id} className="text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-bold text-co-navy">{t.nombre}</span>
                      <span className="tabular font-extrabold text-co-navy">{numFijo(t.peso, 2)}</span>
                    </div>
                    <Barra pct={t.peso * 100} color="bg-co-amber" retraso={i * 80} />
                  </li>
                ))}
              </ul>
            </ReglaCard>
          </div>
        </>
      )}
    </div>
  );
}
