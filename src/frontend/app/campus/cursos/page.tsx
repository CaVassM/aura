"use client";

import Link from "next/link";
import { AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, CalendarClock, Clock, MapPin, UserRound } from "lucide-react";
import Anillo from "@/components/campus/academico/Anillo";
import Pagina, { Esqueleto } from "@/components/campus/academico/Pagina";
import { ColorCurso, colorDeCurso } from "@/components/campus/academico/colores";
import { useAcademico } from "@/components/campus/academico/useAcademico";
import { useCuentaAnimada, useListo } from "@/components/campus/academico/useCuentaAnimada";
import { usePerfil } from "@/components/campus/PerfilProvider";
import { EstadoError } from "@/components/ui/Estados";
import { getCursos } from "@/lib/api";
import { enDias, fechaLarga, numFijo, porcentaje, rangoSinAnio } from "@/lib/format";
import { CursoAcademico, PeriodoAcademico, RespuestaCursos } from "@/lib/types-academico";

const DIAS_CORTOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
const PX_POR_HORA = 44;

const horaDecimal = (hhmm: string) => {
  const [h, m] = hhmm.split(":").map(Number);
  return h + m / 60;
};

/** Posición (0–1) de una fecha dentro del período, para marcar las semanas de evaluación en la barra. */
function posicion(periodo: PeriodoAcademico, iso: string) {
  const t = (s: string) => Date.parse(`${s}T00:00:00Z`);
  return Math.min(Math.max((t(iso) - t(periodo.inicio)) / (t(periodo.fin) - t(periodo.inicio)), 0), 1);
}

function Portada({ datos }: { datos: RespuestaCursos }) {
  const { periodo, asistencia } = datos;
  const listo = useListo(150);
  const tasa = useCuentaAnimada(asistencia.tasa * 100, 1200, 150);
  const baja = asistencia.variacion < 0;
  const semanas = [periodo.evaluacion_actual, periodo.proxima_evaluacion].filter((s) => s !== null);
  const aviso = periodo.evaluacion_actual
    ? `${periodo.evaluacion_actual.titulo} · ${rangoSinAnio(periodo.evaluacion_actual.inicio, periodo.evaluacion_actual.fin)}`
    : periodo.proxima_evaluacion
      ? `${periodo.proxima_evaluacion.titulo} ${enDias(periodo.proxima_evaluacion.dias_para_inicio)}`
      : null;

  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-co-teal to-co-teal-deep px-7 py-7 text-white shadow-lift animate-rise">
      <span className="pointer-events-none absolute -right-10 -top-12 h-44 w-44 rounded-full bg-white/10" aria-hidden="true" />
      <span className="pointer-events-none absolute -bottom-24 left-1/3 h-48 w-48 rounded-full bg-co-coral/20" aria-hidden="true" />
      <span className="pointer-events-none absolute right-40 top-6 h-10 w-10 animate-breathe rounded-full bg-co-amber/30" aria-hidden="true" />

      <div className="relative flex flex-wrap items-center justify-between gap-x-8 gap-y-6">
        <div className="min-w-0 flex-1 basis-72">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal-tint">{datos.estudiante.carrera}</p>
          <p className="mt-1 text-3xl font-extrabold leading-tight tracking-tight">{periodo.nombre}</p>
          <p className="mt-1 text-sm text-co-teal-tint">
            Semana {periodo.semana_actual} de {periodo.total_semanas} · {rangoSinAnio(periodo.inicio, periodo.fin)} · faltan {periodo.dias_para_cierre} días para el cierre
          </p>

          <div className="relative mt-5 h-3 rounded-full bg-white/15" role="progressbar" aria-valuenow={periodo.avance_pct} aria-valuemin={0} aria-valuemax={100} aria-label="Avance del período">
            <div
              className="relative h-full overflow-hidden rounded-full bg-white transition-[width] duration-[1400ms] ease-out"
              style={{ width: listo ? `${periodo.avance_pct}%` : "0%" }}
            >
              <span className="sheen-barra absolute inset-y-0 w-1/3 animate-sheen" aria-hidden="true" />
            </div>
            {semanas.map((s) => {
              const ini = posicion(periodo, s.inicio);
              const fin = posicion(periodo, s.fin);
              return (
                <span
                  key={s.inicio}
                  title={s.titulo}
                  className="absolute -top-1 h-5 rounded-full bg-co-amber/90 ring-2 ring-co-teal-deep"
                  style={{ left: `${ini * 100}%`, width: `max(${(fin - ini) * 100}%, 10px)` }}
                  aria-hidden="true"
                />
              );
            })}
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] font-bold text-co-teal-tint">
            <span>{fechaLarga(periodo.inicio)}</span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-co-amber" aria-hidden="true" />
              Semanas de evaluación
            </span>
            <span>{fechaLarga(periodo.fin)}</span>
          </div>

          {aviso && (
            <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs font-bold">
              <CalendarClock size={14} aria-hidden="true" />
              {aviso}
            </p>
          )}
        </div>

        <div className="flex items-center gap-4">
          <Anillo valor={asistencia.tasa} marca={asistencia.minimo}>
            <span className="tabular text-3xl font-extrabold leading-none">{Math.round(tasa)}</span>
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-co-teal-tint">% asistencia</span>
          </Anillo>
          <div className="max-w-[10rem]">
            <p className="text-sm font-extrabold">Tu asistencia</p>
            <p className="mt-0.5 text-xs text-co-teal-tint">
              {asistencia.asistidas} de {asistencia.sesiones} sesiones
            </p>
            <p className="mt-2 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] font-bold">
              {baja ? <ArrowDownRight size={12} aria-hidden="true" /> : <ArrowUpRight size={12} aria-hidden="true" />}
              {baja ? "" : "+"}
              {Math.round(asistencia.variacion * 100)} pts vs. período anterior ({porcentaje(asistencia.tasa_anterior)})
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Dato({ etiqueta, valor, detalle, retraso }: { etiqueta: string; valor: string; detalle?: string; retraso: number }) {
  return (
    <div className="rounded-2xl border border-co-line bg-white px-5 py-4 shadow-card animate-rise" style={{ animationDelay: `${retraso}ms` }}>
      <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-co-teal">{etiqueta}</p>
      <p className="tabular mt-1 text-2xl font-extrabold text-co-navy">{valor}</p>
      {detalle && <p className="mt-0.5 text-xs font-semibold text-co-ink">{detalle}</p>}
    </div>
  );
}

function BarraAsistencia({ curso, minimo, color }: { curso: CursoAcademico; minimo: number; color: ColorCurso }) {
  const listo = useListo(250);
  const a = curso.asistencia;
  return (
    <div>
      <div className="flex items-baseline justify-between text-xs font-bold">
        <span className="text-co-ink">Asistencia</span>
        <span className={`tabular ${a.bajo_minimo ? "text-co-coral-ink" : "text-co-navy"}`}>
          {a.asistidas} de {a.sesiones} · {porcentaje(a.tasa)}
        </span>
      </div>
      <div className="relative mt-1.5 h-2.5 rounded-full bg-co-bg">
        <div
          className={`h-full rounded-full transition-[width] duration-[1100ms] ease-out ${a.bajo_minimo ? "bg-co-coral" : color.solido}`}
          style={{ width: listo ? `${a.tasa * 100}%` : "0%" }}
        />
        <span
          className="absolute -top-1 w-0.5 rounded bg-co-navy/60"
          style={{ left: `${minimo * 100}%`, height: "1.125rem" }}
          title={`Mínimo ${porcentaje(minimo)}`}
          aria-hidden="true"
        />
      </div>
      {a.bajo_minimo && (
        <p className="mt-1.5 flex items-center gap-1.5 text-[11px] font-bold text-co-coral-ink">
          <AlertTriangle size={12} aria-hidden="true" />
          Por debajo del mínimo de {porcentaje(minimo)}
        </p>
      )}
    </div>
  );
}

function TarjetaCurso({ curso, indice, minimo }: { curso: CursoAcademico; indice: number; minimo: number }) {
  const color = colorDeCurso(indice);
  const prox = curso.proxima_evaluacion;
  return (
    <article
      className="group relative overflow-hidden rounded-2xl border border-co-line bg-white shadow-card transition duration-300 animate-rise hover:-translate-y-1 hover:shadow-lift"
      style={{ animationDelay: `${240 + indice * 90}ms` }}
    >
      <span className={`absolute inset-x-0 top-0 h-1.5 origin-left animate-grow-x ${color.solido}`} style={{ animationDelay: `${300 + indice * 90}ms` }} aria-hidden="true" />
      <div className="space-y-4 px-5 pb-5 pt-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <span className={`inline-block rounded-md px-2 py-0.5 text-[11px] font-extrabold tracking-wide ${color.tinte} ${color.tinta}`}>{curso.codigo}</span>
            <h3 className="mt-1.5 text-lg font-extrabold leading-snug text-co-navy">{curso.nombre}</h3>
            <p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-co-ink">
              <UserRound size={13} aria-hidden="true" />
              {curso.docente}
            </p>
            <p className="mt-0.5 flex items-center gap-1.5 text-xs font-semibold text-co-ink">
              <MapPin size={13} aria-hidden="true" />
              {curso.aula}
            </p>
          </div>
          <div className={`flex shrink-0 flex-col items-center rounded-xl px-3 py-2 ${color.tinte} ${color.tinta}`} title="Promedio parcial">
            <span className="tabular text-xl font-extrabold leading-none">{curso.promedio_parcial !== null ? numFijo(curso.promedio_parcial, 1) : "–"}</span>
            <span className="mt-0.5 text-[9px] font-extrabold uppercase tracking-wider">promedio</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {curso.horario.map((b) => (
            <span key={`${b.dia}-${b.inicio}`} className="tabular inline-flex items-center gap-1 rounded-full border border-co-line bg-co-bg/60 px-2.5 py-1 text-[11px] font-bold text-co-navy">
              <Clock size={11} aria-hidden="true" />
              {DIAS_CORTOS[b.dia]} {b.inicio}–{b.fin}
            </span>
          ))}
          <span className="inline-flex items-center rounded-full border border-co-line px-2.5 py-1 text-[11px] font-bold text-co-ink">{curso.creditos} créditos</span>
        </div>

        <BarraAsistencia curso={curso} minimo={minimo} color={color} />

        {prox && (
          <p className="flex items-center gap-2 border-t border-co-line pt-3 text-xs font-semibold text-co-ink">
            <CalendarClock size={14} className={color.tinta} aria-hidden="true" />
            <span>
              <strong className="text-co-navy">{prox.nombre}</strong> {enDias(prox.dias)} · {prox.peso} % de la nota
            </span>
          </p>
        )}
      </div>
    </article>
  );
}

function Horario({ cursos }: { cursos: CursoAcademico[] }) {
  const bloques = cursos.flatMap((c, i) => c.horario.map((b) => ({ curso: c, color: colorDeCurso(i), b })));
  const desde = Math.floor(Math.min(...bloques.map((x) => horaDecimal(x.b.inicio))));
  const hasta = Math.ceil(Math.max(...bloques.map((x) => horaDecimal(x.b.fin))));
  const horas = Array.from({ length: hasta - desde }, (_, i) => desde + i);
  const alto = (hasta - desde) * PX_POR_HORA;
  return (
    <section aria-labelledby="horario" className="animate-rise" style={{ animationDelay: "600ms" }}>
      <h2 id="horario" className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">
        Tu semana tipo
      </h2>
      <div className="mt-3 overflow-x-auto rounded-2xl border border-co-line bg-white p-4 shadow-card">
        <div className="min-w-[620px]">
          <div className="grid grid-cols-[3rem_repeat(6,minmax(0,1fr))] gap-x-1.5 pb-2 text-center text-[11px] font-extrabold uppercase tracking-wider text-co-ink">
            <span />
            {DIAS_CORTOS.map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>
          <div className="grid grid-cols-[3rem_repeat(6,minmax(0,1fr))] gap-x-1.5">
            <div className="relative" style={{ height: alto }}>
              {horas.map((h) => (
                <span key={h} className="tabular absolute right-2 -translate-y-1/2 text-[10px] font-bold text-co-ink/70" style={{ top: (h - desde) * PX_POR_HORA }}>
                  {String(h).padStart(2, "0")}:00
                </span>
              ))}
            </div>
            {DIAS_CORTOS.map((_, dia) => (
              <div key={dia} className="relative rounded-lg bg-co-bg/50" style={{ height: alto }}>
                {horas.map((h) => (
                  <span key={h} className="absolute inset-x-0 border-t border-co-line/70" style={{ top: (h - desde) * PX_POR_HORA }} aria-hidden="true" />
                ))}
                {bloques
                  .filter((x) => x.b.dia === dia)
                  .map((x, n) => (
                    <div
                      key={`${x.curso.id}-${x.b.inicio}`}
                      className={`absolute inset-x-0.5 overflow-hidden rounded-lg px-2 py-1 text-white shadow-card animate-rise ${x.color.solido}`}
                      style={{
                        top: (horaDecimal(x.b.inicio) - desde) * PX_POR_HORA + 1,
                        height: (horaDecimal(x.b.fin) - horaDecimal(x.b.inicio)) * PX_POR_HORA - 2,
                        animationDelay: `${700 + n * 80 + dia * 40}ms`,
                      }}
                      title={`${x.curso.nombre} · ${x.curso.aula}`}
                    >
                      <p className="truncate text-[11px] font-extrabold leading-tight">{x.curso.codigo}</p>
                      <p className="truncate text-[10px] font-semibold leading-tight opacity-90">{x.curso.nombre}</p>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function CursosPage() {
  const { perfil } = usePerfil();
  const { datos, error, reintentar } = useAcademico(getCursos, perfil.id);

  return (
    <Pagina
      href="/campus/cursos"
      titulo="Mis cursos"
      subtitulo={datos ? `${datos.cursos.length} cursos · ${datos.creditos} créditos · ${datos.periodo.nombre}` : "Cursos del período"}
    >
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !datos ? (
        <Esqueleto bloques={[200, 90, 300]} />
      ) : (
        <>
          <Portada datos={datos} />
          <div className="grid gap-3 sm:grid-cols-3">
            <Dato etiqueta="Cursos" valor={String(datos.cursos.length)} detalle={`${datos.creditos} créditos matriculados`} retraso={120} />
            <Dato
              etiqueta="Próxima evaluación"
              valor={datos.periodo.proxima_evaluacion ? enDias(datos.periodo.proxima_evaluacion.dias_para_inicio) : "–"}
              detalle={datos.periodo.proxima_evaluacion ? rangoSinAnio(datos.periodo.proxima_evaluacion.inicio, datos.periodo.proxima_evaluacion.fin) : undefined}
              retraso={180}
            />
            <Dato etiqueta="Cierre del período" valor={enDias(datos.periodo.dias_para_cierre)} detalle={fechaLarga(datos.periodo.fin)} retraso={240} />
          </div>

          <section aria-labelledby="cursos">
            <h2 id="cursos" className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">
              Cursos del período
            </h2>
            <div className="mt-3 grid gap-4 md:grid-cols-2">
              {datos.cursos.map((c, i) => (
                <TarjetaCurso key={c.id} curso={c} indice={i} minimo={datos.asistencia.minimo} />
              ))}
            </div>
          </section>

          <Horario cursos={datos.cursos} />

          <Link
            href="/campus/calificaciones"
            className="co-foco inline-flex items-center gap-2 rounded-full border border-co-line bg-white px-5 py-2.5 text-sm font-bold text-co-teal-dark shadow-card transition hover:border-co-teal hover:bg-co-teal-tint"
          >
            <BookOpen size={15} aria-hidden="true" />
            Ver mis calificaciones
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </>
      )}
    </Pagina>
  );
}
