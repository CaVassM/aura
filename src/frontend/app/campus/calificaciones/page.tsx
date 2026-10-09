"use client";

import { useState } from "react";
import { ArrowDownRight, ArrowUpRight, CheckCircle2, ChevronDown, Clock3, Target } from "lucide-react";
import Pagina, { Esqueleto } from "@/components/campus/academico/Pagina";
import { colorDeCurso } from "@/components/campus/academico/colores";
import { useAcademico } from "@/components/campus/academico/useAcademico";
import { useCuentaAnimada, useListo } from "@/components/campus/academico/useCuentaAnimada";
import { usePerfil } from "@/components/campus/PerfilProvider";
import { EstadoError } from "@/components/ui/Estados";
import { getCalificaciones } from "@/lib/api";
import { enDias, fechaCorta, numFijo } from "@/lib/format";
import { EvaluacionCurso, NotasCurso, RespuestaCalificaciones } from "@/lib/types-academico";

type Escala = RespuestaCalificaciones["escala"];

/** Color de una nota según dónde cae en la escala. */
function tonoNota(nota: number, escala: Escala) {
  if (nota < escala.aprobatoria) return { fondo: "bg-co-coral-tint", texto: "text-co-coral-ink", barra: "bg-co-coral" };
  if (nota < 5.5) return { fondo: "bg-co-amber-tint", texto: "text-co-amber-ink", barra: "bg-co-amber" };
  return { fondo: "bg-co-sage-tint", texto: "text-co-sage-ink", barra: "bg-co-sage" };
}

const pos = (nota: number, e: Escala) => ((nota - e.minima) / (e.maxima - e.minima)) * 100;

/** Regla 1,0–7,0 con la marca de aprobación (4,0), el promedio anterior y el actual. */
function Regla({ actual, anterior, escala }: { actual: number; anterior: number; escala: Escala }) {
  const listo = useListo(250);
  return (
    <div className="relative mt-8 pb-7">
      <div className="relative h-3 rounded-full bg-white/15">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-co-coral via-co-amber to-co-sage opacity-40"
          style={{ width: "100%" }}
          aria-hidden="true"
        />
        <span className="absolute -top-1 h-5 w-0.5 bg-white/80" style={{ left: `${pos(escala.aprobatoria, escala)}%` }} aria-hidden="true" />
        <span
          className="absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/70 bg-co-teal-deep"
          style={{ left: `${pos(anterior, escala)}%` }}
          title={`Período anterior: ${numFijo(anterior, 1)}`}
          aria-hidden="true"
        />
        <span
          className="absolute top-1/2 h-6 w-6 -translate-y-1/2 rounded-full border-4 border-white bg-co-amber shadow-pop transition-[left] duration-[1400ms] ease-out"
          style={{ left: listo ? `calc(${pos(actual, escala)}% - 12px)` : "-12px" }}
          aria-hidden="true"
        />
      </div>
      <div className="tabular absolute inset-x-0 bottom-0 flex text-[11px] font-bold text-co-teal-tint">
        <span className="absolute -translate-x-1/2" style={{ left: "0%" }}>{numFijo(escala.minima, 1)}</span>
        <span className="absolute -translate-x-1/2 text-white" style={{ left: `${pos(escala.aprobatoria, escala)}%` }}>{numFijo(escala.aprobatoria, 1)} aprueba</span>
        <span className="absolute -translate-x-full" style={{ left: "100%" }}>{numFijo(escala.maxima, 1)}</span>
      </div>
      <span className="sr-only">Promedio {numFijo(actual, 1)} sobre {numFijo(escala.maxima, 1)}</span>
    </div>
  );
}

function Portada({ datos }: { datos: RespuestaCalificaciones }) {
  const general = datos.promedio_general ?? 0;
  const cuenta = useCuentaAnimada(general, 1300, 150);
  const baja = (datos.variacion ?? 0) < 0;
  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-co-teal to-co-teal-deep px-7 py-7 text-white shadow-lift animate-rise">
      <span className="pointer-events-none absolute -right-12 -top-12 h-48 w-48 rounded-full bg-white/10" aria-hidden="true" />
      <span className="pointer-events-none absolute -bottom-24 right-1/4 h-48 w-48 rounded-full bg-co-coral/20" aria-hidden="true" />
      <span className="pointer-events-none absolute right-24 top-8 h-10 w-10 animate-breathe rounded-full bg-co-amber/30" aria-hidden="true" />
      <div className="relative">
        <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal-tint">Promedio del período · {datos.periodo.nombre}</p>
        <div className="mt-2 flex flex-wrap items-end gap-x-6 gap-y-2">
          <p className="tabular text-6xl font-extrabold leading-none tracking-tight">{numFijo(cuenta, 1)}</p>
          <div className="pb-1">
            {datos.variacion !== null && (
              <p className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-extrabold ${baja ? "bg-co-coral/30" : "bg-co-sage/40"}`}>
                {baja ? <ArrowDownRight size={14} aria-hidden="true" /> : <ArrowUpRight size={14} aria-hidden="true" />}
                {baja ? "" : "+"}
                {numFijo(datos.variacion, 1)} vs. período anterior
              </p>
            )}
            <p className="mt-1.5 text-xs text-co-teal-tint">
              Período anterior: <strong className="text-white">{numFijo(datos.promedio_anterior, 1)}</strong> · ponderado por créditos, solo con las notas ya publicadas
            </p>
          </div>
        </div>
        {datos.promedio_general !== null && <Regla actual={general} anterior={datos.promedio_anterior} escala={datos.escala} />}
      </div>
    </section>
  );
}

function PillNota({ ev, escala }: { ev: EvaluacionCurso; escala: Escala }) {
  if (ev.nota !== null) {
    const t = tonoNota(ev.nota, escala);
    return <span className={`tabular rounded-lg px-2.5 py-1 text-sm font-extrabold ${t.fondo} ${t.texto}`}>{numFijo(ev.nota, 1)}</span>;
  }
  if (ev.estado === "sin_publicar")
    return (
      <span className="inline-flex items-center gap-1 rounded-lg bg-co-amber-tint px-2.5 py-1 text-[11px] font-extrabold text-co-amber-ink">
        <Clock3 size={12} aria-hidden="true" />
        Sin publicar
      </span>
    );
  return <span className="rounded-lg border border-dashed border-co-line px-2.5 py-1 text-[11px] font-bold text-co-ink">Pendiente</span>;
}

function Mensaje({ curso }: { curso: NotasCurso }) {
  switch (curso.situacion) {
    case "sin_notas":
      return <>Aún no hay notas publicadas.</>;
    case "asegurado":
      return (
        <>
          <CheckCircle2 size={14} className="shrink-0 text-co-sage-ink" aria-hidden="true" />
          Ya tienes asegurado el 4,0 con lo evaluado.
        </>
      );
    case "alcanzable":
      return (
        <>
          <Target size={14} className="shrink-0 text-co-teal" aria-hidden="true" />
          Necesitas un promedio de <strong className="text-co-navy">{numFijo(curso.nota_necesaria ?? 0, 1)}</strong> en lo que falta para llegar a 4,0.
        </>
      );
    case "fuera_de_alcance":
      return <>Con lo que falta no se llega a 4,0 solo con evaluaciones; conversa con tu docente.</>;
    case "aprobado":
      return <>Curso aprobado.</>;
    default:
      return <>Curso reprobado.</>;
  }
}

function TarjetaNotas({ curso, indice, escala, hoy, abierta: abiertaInicial }: { curso: NotasCurso; indice: number; escala: Escala; hoy: string; abierta: boolean }) {
  const [abierta, setAbierta] = useState(abiertaInicial);
  const listo = useListo(200 + indice * 90);
  const color = colorDeCurso(indice);
  const tono = curso.promedio_parcial !== null ? tonoNota(curso.promedio_parcial, escala) : null;
  return (
    <article
      className="relative overflow-hidden rounded-2xl border border-co-line bg-white shadow-card animate-rise transition duration-300 hover:shadow-lift"
      style={{ animationDelay: `${200 + indice * 90}ms` }}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${color.solido}`} aria-hidden="true" />
      <button
        onClick={() => setAbierta((a) => !a)}
        aria-expanded={abierta}
        className="co-foco flex w-full items-center gap-4 py-4 pl-6 pr-5 text-left"
      >
        <div className="min-w-0 flex-1">
          <span className={`inline-block rounded-md px-2 py-0.5 text-[11px] font-extrabold ${color.tinte} ${color.tinta}`}>{curso.codigo}</span>
          <p className="mt-1 truncate text-base font-extrabold text-co-navy">{curso.nombre}</p>
          <p className="text-xs font-semibold text-co-ink">{curso.creditos} créditos · {curso.peso_evaluado} % evaluado</p>
        </div>
        <div className={`flex h-14 w-16 shrink-0 flex-col items-center justify-center rounded-xl ${tono ? `${tono.fondo} ${tono.texto}` : "bg-co-bg text-co-ink"}`}>
          <span className="tabular text-xl font-extrabold leading-none">{curso.promedio_parcial !== null ? numFijo(curso.promedio_parcial, 1) : "–"}</span>
          <span className="mt-0.5 text-[9px] font-extrabold uppercase tracking-wider">parcial</span>
        </div>
        <ChevronDown size={18} className={`shrink-0 text-co-ink transition-transform duration-300 ${abierta ? "rotate-180" : ""}`} aria-hidden="true" />
      </button>

      {/* Barra de composición: cada tramo es una evaluación (ancho = peso); se llena con su nota. */}
      <div className="px-6 pb-4">
        <div className="flex h-3 gap-0.5 overflow-hidden rounded-full" aria-hidden="true">
          {curso.evaluaciones.map((ev, i) => {
            const t = ev.nota !== null ? tonoNota(ev.nota, escala) : null;
            return (
              <div key={ev.tipo} className="relative h-full bg-co-bg" style={{ width: `${ev.peso}%` }} title={`${ev.nombre} · ${ev.peso} %`}>
                {t && (
                  <div
                    className={`h-full origin-left transition-[width] duration-[900ms] ease-out ${t.barra}`}
                    style={{ width: listo ? "100%" : "0%", transitionDelay: `${i * 140}ms` }}
                  />
                )}
              </div>
            );
          })}
        </div>
        <p className="mt-2.5 flex items-start gap-1.5 text-xs font-semibold text-co-ink">
          <Mensaje curso={curso} />
        </p>
      </div>

      <div className={`grid transition-all duration-300 ease-out ${abierta ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
        <div className="overflow-hidden">
          <ul className="divide-y divide-co-line border-t border-co-line">
            {curso.evaluaciones.map((ev) => (
              <li key={ev.tipo} className="flex items-center gap-3 py-3 pl-6 pr-5">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-co-navy">{ev.nombre}</p>
                  <p className="text-xs font-semibold text-co-ink">
                    {fechaCorta(ev.fecha)} · {ev.peso} % de la nota
                    {ev.estado === "programada" && ` · ${enDias(Math.round((Date.parse(`${ev.fecha}T00:00:00Z`) - Date.parse(`${hoy}T00:00:00Z`)) / 86400000))}`}
                  </p>
                </div>
                <PillNota ev={ev} escala={escala} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

export default function CalificacionesPage() {
  const { perfil } = usePerfil();
  const { datos, error, reintentar } = useAcademico(getCalificaciones, perfil.id);

  return (
    <Pagina
      href="/campus/calificaciones"
      titulo="Calificaciones"
      subtitulo={datos ? `${datos.periodo.nombre} · escala ${numFijo(datos.escala.minima, 1)} a ${numFijo(datos.escala.maxima, 1)}` : "Notas del período"}
      ancho="max-w-4xl"
    >
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !datos ? (
        <Esqueleto bloques={[220, 130, 130, 130]} />
      ) : (
        <>
          <Portada datos={datos} />
          <section aria-labelledby="por-curso" className="space-y-3">
            <h2 id="por-curso" className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">
              Por curso
            </h2>
            {datos.cursos.map((c, i) => (
              <TarjetaNotas key={`${perfil.id}-${c.id}`} curso={c} indice={i} escala={datos.escala} hoy={datos.periodo.hoy} abierta={i === 0} />
            ))}
            <p className="px-1 text-xs font-medium leading-relaxed text-co-ink">
              Las notas de esta vista son una simulación para la demo. El promedio parcial usa solo las evaluaciones ya publicadas; la nota
              que falta para aprobar supone que las pendientes pesan lo indicado.
            </p>
          </section>
        </>
      )}
    </Pagina>
  );
}
