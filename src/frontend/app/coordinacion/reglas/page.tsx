"use client";

import { Info, LockKeyhole } from "lucide-react";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import { useApi } from "@/components/coordinacion/useApi";
import ReglaCard from "@/components/coordinacion/reglas/ReglaCard";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getReglas } from "@/lib/api";
import { num, numFijo } from "@/lib/format";

const texto = (umbral: number | string | string[]) =>
  Array.isArray(umbral)
    ? umbral.join(" o ")
    : typeof umbral === "number"
      ? num(umbral, 2)
      : umbral;

export default function ReglasPage() {
  const { data: r, error, cargando, reintentar } = useApi(() => getReglas(), []);

  return (
    <CoordinacionShell activeHref="/coordinacion/reglas">
      <div className="mx-auto max-w-5xl space-y-6 px-8 py-8">
        <div className="flex flex-col gap-4 border-b border-aura-border pb-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs font-bold tracking-wide text-aura-teal">REGLAS</p>
            <h2 className="mt-1.5 text-3xl font-bold text-aura-navy">
              Estas reglas guían a AURA.
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-aura-gray">
              Se ajustan con la aprobación del equipo de bienestar, sin
              reprogramar el sistema. Lo marcado como provisional son supuestos
              del prototipo.
            </p>
          </div>
          <span
            title="Se modifica en los archivos de configuración con aprobación de bienestar"
            className="inline-flex shrink-0 items-center gap-2 rounded-full border border-aura-border bg-white px-4 py-2 text-xs font-semibold text-aura-gray"
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
            <ReglaCard numero="01" titulo="Motivo → servicio" provisional={r.motivo_servicio.provisional}>
              <div className="divide-y divide-aura-border rounded-xl border border-aura-border">
                {r.motivo_servicio.items.map((m) => (
                  <div
                    key={m.motivo}
                    className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-3 text-sm"
                  >
                    <span className="font-medium text-aura-navy">{m.motivo_label}</span>
                    <span className="text-aura-teal">→</span>
                    <span className="text-right font-bold text-aura-teal-dark">
                      {m.servicio_label}
                    </span>
                  </div>
                ))}
              </div>
            </ReglaCard>

            <ReglaCard numero="02" titulo="Afinidad" provisional={r.afinidad.provisional}>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[420px] text-center text-sm">
                  <thead>
                    <tr>
                      <th className="p-3 text-left text-xs font-semibold text-aura-gray">
                        Necesita ↓ · Servicio →
                      </th>
                      {r.afinidad.tipos.map((t) => (
                        <th key={t.codigo} className="p-3 text-aura-navy">
                          {t.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {r.afinidad.matriz.map((fila) => (
                      <tr key={fila.ideal}>
                        <th className="p-3 text-left text-aura-navy">{fila.ideal_label}</th>
                        {fila.valores.map((v) => {
                          const alternativa =
                            v.tipo !== fila.ideal && v.valor >= r.afinidad.minimo_alternativa;
                          return (
                            <td
                              key={v.tipo}
                              className={`rounded-lg p-3 ${alternativa ? "bg-[#E6F4F0] font-bold text-aura-teal-dark" : "bg-aura-bg"}`}
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
              <div className="mt-4 rounded-xl bg-aura-teal-pale p-3 text-sm text-aura-gray">
                Mínimo para ofrecer alternativa:{" "}
                <strong className="text-aura-teal-dark">
                  {numFijo(r.afinidad.minimo_alternativa, 1)}
                </strong>
                {r.afinidad.minimo_provisional && " (provisional)"}. Las celdas
                resaltadas son alternativas permitidas.
              </div>
            </ReglaCard>

            <ReglaCard numero="03" titulo="Aviso académico" provisional={r.aviso.provisional}>
              <div className="grid gap-3 md:grid-cols-2">
                {r.aviso.senales.map((s) => (
                  <div
                    key={s.id}
                    className="flex gap-3 rounded-xl bg-aura-bg p-3 text-sm text-aura-navy"
                  >
                    <span className="font-extrabold text-aura-teal">{s.id}</span>
                    <span>
                      <span className="block font-semibold">{s.nombre}</span>
                      <span className="block text-aura-gray">{s.descripcion}</span>
                      <span className="mt-0.5 block text-xs text-aura-gray">
                        Umbral: {texto(s.umbral)}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex gap-3 rounded-xl border border-aura-tag-red-bg bg-[#FFF9F7] p-4 text-sm leading-6 text-aura-gray">
                <Info className="mt-0.5 h-5 w-5 shrink-0 text-aura-tag-red-text" aria-hidden="true" />
                <span>
                  Se muestra aviso únicamente con {r.aviso.puntaje_minimo} o más
                  señales
                  {r.aviso.solo_semanas_evaluacion &&
                    " y solo durante semanas de evaluaciones"}
                  . Estas señales nunca se muestran al estudiante.
                </span>
              </div>
            </ReglaCard>

            <div className="grid gap-6 lg:grid-cols-2">
              <ReglaCard numero="04" titulo="Probabilidad de asistencia" provisional={r.p_asistencia.provisional}>
                <div className="space-y-3">
                  {r.p_asistencia.canales.map((c) => (
                    <div
                      key={c.canal}
                      className="flex items-center justify-between border-b border-aura-border pb-3 text-sm last:border-0 last:pb-0"
                    >
                      <span className="text-aura-navy">{c.canal_label}</span>
                      <span className="font-extrabold text-aura-teal-dark">
                        {numFijo(c.valor, 3)}
                      </span>
                    </div>
                  ))}
                </div>
              </ReglaCard>

              <ReglaCard numero="05" titulo="Pesos del motor" provisional={r.pesos.provisional}>
                <div className="space-y-3">
                  {r.pesos.terminos.map((t) => (
                    <div key={t.id} className="flex items-center gap-3 text-sm">
                      <span className="w-40 shrink-0 text-aura-gray">{t.nombre}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-aura-bg">
                        <div
                          className="h-full rounded-full bg-aura-teal"
                          style={{ width: `${t.peso * 100}%` }}
                        />
                      </div>
                      <span className="w-10 text-right font-extrabold text-aura-navy">
                        {numFijo(t.peso, 2)}
                      </span>
                    </div>
                  ))}
                </div>
              </ReglaCard>
            </div>
          </>
        )}
      </div>
    </CoordinacionShell>
  );
}
