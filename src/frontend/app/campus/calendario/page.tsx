"use client";

import { ReactNode, useEffect, useMemo, useState } from "react";
import { BookOpen, CalendarCheck, ChevronLeft, ChevronRight, Flag, FileText, HeartHandshake, Leaf, PartyPopper, Sparkles } from "lucide-react";
import Pagina, { Esqueleto } from "@/components/campus/academico/Pagina";
import { colorDeCurso } from "@/components/campus/academico/colores";
import { useAcademico } from "@/components/campus/academico/useAcademico";
import { usePerfil } from "@/components/campus/PerfilProvider";
import { EstadoError } from "@/components/ui/Estados";
import { getCalendario, getMisCitas } from "@/lib/api";
import { distritoLabel, fechaConDia, fechaLarga, primeraMayuscula, rangoSinAnio } from "@/lib/format";
import { Cita } from "@/lib/types";
import { EventoCalendario, RespuestaCalendario } from "@/lib/types-academico";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

type Categoria = "clases" | "evaluaciones" | "actividades" | "citas";
const CATEGORIAS: { id: Categoria; etiqueta: string; punto: string }[] = [
  { id: "clases", etiqueta: "Clases", punto: "bg-co-teal" },
  { id: "evaluaciones", etiqueta: "Evaluaciones", punto: "bg-co-coral" },
  { id: "actividades", etiqueta: "Actividades", punto: "bg-co-sage" },
  { id: "citas", etiqueta: "Mis citas", punto: "bg-co-navy" },
];

/** Evento del calendario ya expandido a un día concreto. */
interface Item extends EventoCalendario {
  categoria: Categoria | "banda";
  dia: string;
}

const iso = (d: Date) => d.toISOString().slice(0, 10);
const utc = (s: string) => {
  const [a, m, d] = s.split("-").map(Number);
  return new Date(Date.UTC(a, m - 1, d));
};
const sumarDias = (s: string, n: number) => iso(new Date(utc(s).getTime() + n * 86400000));

function categoriaDe(e: EventoCalendario): Categoria | "banda" {
  switch (e.tipo) {
    case "clase":
      return "clases";
    case "evaluacion":
      return "evaluaciones";
    case "semana_evaluacion":
      return "banda";
    default:
      return "actividades";
  }
}

function celdasDelMes(ym: string): string[] {
  const [a, m] = ym.split("-").map(Number);
  const primero = new Date(Date.UTC(a, m - 1, 1));
  const desfase = (primero.getUTCDay() + 6) % 7;
  const total = Math.ceil((desfase + new Date(Date.UTC(a, m, 0)).getUTCDate()) / 7) * 7;
  return Array.from({ length: total }, (_, i) => iso(new Date(Date.UTC(a, m - 1, 1 - desfase + i))));
}

function citaComoEvento(c: Cita): EventoCalendario {
  const [fecha, hora] = c.slot.fecha_iso.split("T");
  return {
    id: c.id,
    tipo: "actividad_universitaria", // se reclasifica abajo como cita
    titulo: c.servicio_nombre,
    inicio: fecha,
    fin: fecha,
    hora_inicio: hora.slice(0, 5),
    hora_fin: c.hora_fin,
    lugar: c.canal === "in_person" ? `Presencial · ${distritoLabel(c.distrito)}` : c.canal === "phone" ? "Teléfono" : "Videollamada",
  };
}

function Contenido({ datos, citas }: { datos: RespuestaCalendario; citas: Cita[] }) {
  const { periodo } = datos;
  const [mes, setMes] = useState(periodo.hoy.slice(0, 7));
  const [dia, setDia] = useState(periodo.hoy);
  const [activas, setActivas] = useState<Set<Categoria>>(new Set(["clases", "evaluaciones", "actividades", "citas"]));
  const [sentido, setSentido] = useState<1 | -1>(1);

  const indiceCurso = useMemo(() => new Map(datos.cursos.map((c, i) => [c.id, i])), [datos.cursos]);
  const nombreCurso = useMemo(() => new Map(datos.cursos.map((c) => [c.id, c.codigo])), [datos.cursos]);

  // Cada evento se reparte en los días que cubre.
  const porDia = useMemo(() => {
    const mapa = new Map<string, Item[]>();
    const poner = (e: EventoCalendario, categoria: Item["categoria"]) => {
      for (let d = e.inicio; d <= e.fin; d = sumarDias(d, 1)) {
        const lista = mapa.get(d) ?? [];
        lista.push({ ...e, categoria, dia: d });
        mapa.set(d, lista);
      }
    };
    datos.eventos.forEach((e) => poner(e, categoriaDe(e)));
    citas.filter((c) => c.estado === "confirmada").forEach((c) => poner({ ...citaComoEvento(c), id: `cita-${c.id}` }, "citas"));
    mapa.forEach((l) => l.sort((a, b) => (a.hora_inicio ?? "00:00").localeCompare(b.hora_inicio ?? "00:00")));
    return mapa;
  }, [datos.eventos, citas]);

  const semanasEvaluacion = datos.eventos.filter((e) => e.tipo === "semana_evaluacion");
  const semanaDe = (d: string) => semanasEvaluacion.find((s) => s.inicio <= d && d <= s.fin);

  const primerMes = periodo.inicio.slice(0, 7);
  const ultimoMes = periodo.fin.slice(0, 7);
  const [anio, nMes] = mes.split("-").map(Number);
  const irA = (ym: string) => {
    if (ym < primerMes || ym > ultimoMes) return;
    setSentido(ym > mes ? 1 : -1);
    setMes(ym);
  };
  const vecino = (n: number) => iso(new Date(Date.UTC(anio, nMes - 1 + n, 1))).slice(0, 7);

  const alternar = (c: Categoria) =>
    setActivas((s) => {
      const n = new Set(s);
      if (n.has(c)) n.delete(c);
      else n.add(c);
      return n;
    });

  const visibles = (d: string) => (porDia.get(d) ?? []).filter((i) => i.categoria === "banda" || activas.has(i.categoria));
  const delDia = visibles(dia).filter((i) => i.categoria !== "banda");
  const bandaDia = semanaDe(dia);

  // Si se cambia de mes con el día elegido fuera, se elige el 1.º o «hoy» si cae dentro.
  useEffect(() => {
    if (dia.slice(0, 7) !== mes) setDia(periodo.hoy.slice(0, 7) === mes ? periodo.hoy : `${mes}-01`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mes]);

  return (
    <>
      {/* Resumen del período */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-co-amber/40 bg-co-amber-tint px-6 py-4 animate-rise">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-amber-ink">
            <CalendarCheck size={14} aria-hidden="true" />
            {periodo.nombre} · semana {periodo.semana_actual} de {periodo.total_semanas}
          </p>
          <p className="mt-1 text-sm font-extrabold text-co-navy">
            {periodo.evaluacion_actual
              ? `${periodo.evaluacion_actual.titulo} · ${rangoSinAnio(periodo.evaluacion_actual.inicio, periodo.evaluacion_actual.fin)}`
              : periodo.proxima_evaluacion
                ? `Próximas evaluaciones: ${rangoSinAnio(periodo.proxima_evaluacion.inicio, periodo.proxima_evaluacion.fin)}`
                : "Sin evaluaciones pendientes"}
          </p>
        </div>
        {periodo.evaluacion_actual && periodo.proxima_evaluacion && (
          <p className="text-xs font-bold text-co-amber-ink">
            Después: {periodo.proxima_evaluacion.titulo.toLowerCase()} · {rangoSinAnio(periodo.proxima_evaluacion.inicio, periodo.proxima_evaluacion.fin)}
          </p>
        )}
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <section className="rounded-3xl border border-co-line bg-white p-4 shadow-card animate-rise sm:p-5" style={{ animationDelay: "80ms" }}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1">
              <button
                onClick={() => irA(vecino(-1))}
                disabled={vecino(-1) < primerMes}
                aria-label="Mes anterior"
                className="co-foco flex h-9 w-9 items-center justify-center rounded-full text-co-navy transition hover:bg-co-bg disabled:opacity-30"
              >
                <ChevronLeft size={18} aria-hidden="true" />
              </button>
              <h2 className="min-w-[10.5rem] text-center text-xl font-extrabold capitalize text-co-navy">
                {MESES[nMes - 1]} {anio}
              </h2>
              <button
                onClick={() => irA(vecino(1))}
                disabled={vecino(1) > ultimoMes}
                aria-label="Mes siguiente"
                className="co-foco flex h-9 w-9 items-center justify-center rounded-full text-co-navy transition hover:bg-co-bg disabled:opacity-30"
              >
                <ChevronRight size={18} aria-hidden="true" />
              </button>
            </div>
            <button
              onClick={() => {
                setSentido(periodo.hoy.slice(0, 7) > mes ? 1 : -1);
                setMes(periodo.hoy.slice(0, 7));
                setDia(periodo.hoy);
              }}
              className="co-foco rounded-full border border-co-line px-4 py-1.5 text-xs font-extrabold text-co-teal-dark transition hover:border-co-teal hover:bg-co-teal-tint"
            >
              Ir a hoy
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Qué mostrar">
            {CATEGORIAS.map((c) => {
              const on = activas.has(c.id);
              return (
                <button
                  key={c.id}
                  onClick={() => alternar(c.id)}
                  aria-pressed={on}
                  className={`co-foco inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold transition ${
                    on ? "border-co-teal bg-co-teal-tint text-co-teal-dark" : "border-co-line text-co-ink opacity-70 hover:opacity-100"
                  }`}
                >
                  <span className={`h-2 w-2 rounded-full ${on ? c.punto : "bg-co-line"}`} aria-hidden="true" />
                  {c.etiqueta}
                </button>
              );
            })}
          </div>

          <div className="mt-4 grid grid-cols-7 gap-1 text-center text-[11px] font-extrabold uppercase tracking-wider text-co-ink sm:gap-1.5">
            {DIAS.map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>

          <div
            key={mes}
            className={`mt-1.5 grid grid-cols-7 gap-1 sm:gap-1.5 ${sentido === 1 ? "animate-slide-in-right" : "animate-fade-in"}`}
          >
            {celdasDelMes(mes).map((d, i) => {
              const fuera = d.slice(0, 7) !== mes;
              const items = visibles(d);
              const banda = semanaDe(d);
              const esHoy = d === periodo.hoy;
              const elegido = d === dia;
              const enPeriodo = d >= periodo.inicio && d <= periodo.fin;
              const clases = items.filter((x) => x.categoria === "clases");
              const destacados = items.filter((x) => x.categoria !== "clases" && x.categoria !== "banda");
              return (
                <button
                  key={d}
                  onClick={() => {
                    if (fuera) irA(d.slice(0, 7));
                    setDia(d);
                  }}
                  style={{ animationDelay: `${Math.min(i * 12, 300)}ms` }}
                  aria-label={`${fechaConDia(d)}${items.length ? `, ${items.filter((x) => x.categoria !== "banda").length} eventos` : ""}`}
                  aria-pressed={elegido}
                  className={`co-foco relative flex min-h-[56px] flex-col items-stretch overflow-hidden rounded-xl border p-1 text-left transition duration-200 animate-fade-in sm:min-h-[96px] sm:p-1.5 ${
                    elegido ? "border-co-teal ring-2 ring-co-teal/30" : "border-transparent hover:border-co-line hover:bg-co-bg"
                  } ${fuera ? "opacity-40" : ""} ${
                    banda ? (banda.intensidad && banda.intensidad >= 3 ? "bg-co-coral-tint/70" : "bg-co-amber-tint/80") : enPeriodo ? "bg-co-bg/60" : ""
                  }`}
                >
                  <span
                    className={`tabular flex h-6 w-6 items-center justify-center rounded-full text-xs font-extrabold ${
                      esHoy ? "animate-breathe bg-co-teal text-white" : "text-co-navy"
                    }`}
                  >
                    {Number(d.slice(8))}
                  </span>
                  <span className="mt-0.5 hidden min-w-0 flex-col gap-0.5 sm:flex">
                    {destacados.slice(0, 2).map((x) => (
                      <span
                        key={x.id}
                        className={`truncate rounded px-1 py-0.5 text-[10px] font-bold leading-tight ${
                          x.categoria === "evaluaciones"
                            ? "bg-co-coral text-white"
                            : x.categoria === "citas"
                              ? "bg-co-navy text-white"
                              : "bg-co-sage-tint text-co-sage-ink"
                        }`}
                      >
                        {x.categoria === "evaluaciones" ? x.titulo.split(" · ")[0] : x.titulo}
                      </span>
                    ))}
                    {destacados.length > 2 && <span className="text-[10px] font-bold text-co-ink">+{destacados.length - 2} más</span>}
                  </span>
                  {clases.length > 0 && (
                    <span className="mt-auto flex flex-wrap gap-0.5 pt-1">
                      {clases.map((x) => (
                        <span
                          key={x.id}
                          className={`h-1.5 w-1.5 rounded-full sm:h-2 sm:w-2 ${
                            x.estado === "falto" ? "bg-co-coral ring-2 ring-co-coral/30" : colorDeCurso(indiceCurso.get(x.curso_id ?? "") ?? 0).solido
                          }`}
                        />
                      ))}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-co-line pt-3 text-[11px] font-semibold text-co-ink">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-co-amber-tint ring-1 ring-co-amber/50" aria-hidden="true" />
              Evaluaciones intermedias
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-co-coral-tint ring-1 ring-co-coral/50" aria-hidden="true" />
              Evaluaciones finales
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-co-coral ring-2 ring-co-coral/30" aria-hidden="true" />
              Clase a la que faltaste
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-co-teal" aria-hidden="true" />
              Clases (un punto por clase, del color de su curso)
            </span>
          </div>
        </section>

        {/* Agenda del día */}
        <aside className="h-fit rounded-3xl border border-co-line bg-white p-5 shadow-card animate-rise lg:sticky lg:top-4" style={{ animationDelay: "160ms" }} aria-live="polite">
          <div key={dia} className="animate-fade-in">
            <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">{dia === periodo.hoy ? "Hoy" : "Agenda del día"}</p>
            <h3 className="mt-1 text-lg font-extrabold leading-snug text-co-navy">{primeraMayuscula(fechaConDia(dia))}</h3>
            {bandaDia && (
              <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-co-amber-tint px-3 py-1 text-[11px] font-extrabold text-co-amber-ink">
                <FileText size={12} aria-hidden="true" />
                {bandaDia.titulo}
              </p>
            )}
          </div>

          {delDia.length === 0 ? (
            <div key={`vacio-${dia}`} className="mt-6 flex flex-col items-center gap-2 rounded-2xl border border-dashed border-co-line px-4 py-8 text-center animate-rise">
              <span className="flex h-10 w-10 animate-breathe items-center justify-center rounded-full bg-co-sage-tint text-co-sage-ink">
                <Leaf size={18} aria-hidden="true" />
              </span>
              <p className="text-sm font-bold text-co-navy">Sin nada agendado</p>
              <p className="text-xs text-co-ink">Un buen día para descansar o avanzar con calma.</p>
            </div>
          ) : (
            <ul key={`lista-${dia}`} className="mt-4 space-y-2.5">
              {delDia.map((x, n) => (
                <FilaAgenda key={x.id + x.dia} item={x} indice={n} indiceCurso={indiceCurso} nombreCurso={nombreCurso} />
              ))}
            </ul>
          )}
        </aside>
      </div>
    </>
  );
}

function FilaAgenda({
  item,
  indice,
  indiceCurso,
  nombreCurso,
}: {
  item: Item;
  indice: number;
  indiceCurso: Map<string, number>;
  nombreCurso: Map<string, string>;
}) {
  let barra = "bg-co-teal";
  let icono: ReactNode = <Flag size={15} />;
  let insignia: ReactNode = null;
  let detalle: string | null = null;
  const curso = item.curso_id ? indiceCurso.get(item.curso_id) : undefined;

  switch (item.categoria) {
    case "clases": {
      const c = colorDeCurso(curso ?? 0);
      barra = c.solido;
      icono = <BookOpen size={15} />;
      detalle = [nombreCurso.get(item.curso_id ?? ""), item.lugar].filter(Boolean).join(" · ");
      insignia =
        item.estado === "asistio" ? (
          <span className="rounded-md bg-co-sage-tint px-2 py-0.5 text-[10px] font-extrabold text-co-sage-ink">Asististe</span>
        ) : item.estado === "falto" ? (
          <span className="rounded-md bg-co-coral-tint px-2 py-0.5 text-[10px] font-extrabold text-co-coral-ink">Faltaste</span>
        ) : null;
      break;
    }
    case "evaluaciones":
      barra = "bg-co-coral";
      icono = <FileText size={15} />;
      detalle = `${item.peso ?? ""} % de la nota`;
      insignia =
        item.estado === "calificada" ? (
          <span className="rounded-md bg-co-sage-tint px-2 py-0.5 text-[10px] font-extrabold text-co-sage-ink">Con nota</span>
        ) : item.estado === "sin_publicar" ? (
          <span className="rounded-md bg-co-amber-tint px-2 py-0.5 text-[10px] font-extrabold text-co-amber-ink">Sin publicar</span>
        ) : (
          <span className="rounded-md bg-co-coral-tint px-2 py-0.5 text-[10px] font-extrabold text-co-coral-ink">Próxima</span>
        );
      break;
    case "citas":
      barra = "bg-co-navy";
      icono = <HeartHandshake size={15} />;
      detalle = item.lugar ?? null;
      insignia = <span className="rounded-md bg-co-teal-tint px-2 py-0.5 text-[10px] font-extrabold text-co-teal-dark">Bienestar</span>;
      break;
    default:
      if (item.tipo === "bienestar") {
        barra = "bg-co-sage";
        icono = <Leaf size={15} />;
        detalle = item.distrito && item.distrito !== "ALL" ? `Distrito ${distritoLabel(item.distrito)}` : null;
      } else if (item.tipo === "actividad_universitaria") {
        barra = "bg-co-amber";
        icono = <PartyPopper size={15} />;
        detalle = item.distrito && item.distrito !== "ALL" ? `Distrito ${distritoLabel(item.distrito)}` : null;
      } else {
        icono = <Sparkles size={15} />;
      }
  }

  return (
    <li
      className="relative overflow-hidden rounded-xl border border-co-line bg-co-paper py-2.5 pl-4 pr-3 animate-rise"
      style={{ animationDelay: `${indice * 70}ms` }}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${barra}`} aria-hidden="true" />
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 shrink-0 text-co-ink">{icono}</span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-extrabold leading-snug text-co-navy">{item.titulo}</p>
          {item.hora_inicio && (
            <p className="tabular text-xs font-bold text-co-teal-dark">
              {item.hora_inicio}
              {item.hora_fin ? ` – ${item.hora_fin}` : ""}
            </p>
          )}
          {item.fin !== item.inicio && (
            <p className="text-xs font-semibold text-co-ink">
              {fechaLarga(item.inicio)} al {fechaLarga(item.fin)}
            </p>
          )}
          {detalle && <p className="text-xs font-semibold text-co-ink">{detalle}</p>}
        </div>
        {insignia}
      </div>
    </li>
  );
}

export default function CalendarioPage() {
  const { perfil } = usePerfil();
  const { datos, error, reintentar } = useAcademico(getCalendario, perfil.id);
  const [citas, setCitas] = useState<Cita[]>([]);

  useEffect(() => {
    let vigente = true;
    getMisCitas(perfil.id)
      .then((c) => vigente && setCitas(c))
      .catch(() => vigente && setCitas([]));
    return () => {
      vigente = false;
    };
  }, [perfil.id]);

  return (
    <Pagina
      href="/campus/calendario"
      titulo="Calendario"
      subtitulo={datos ? `${datos.periodo.nombre} · calendario académico de tu institución y distrito` : "Calendario académico"}
      ancho="max-w-6xl"
    >
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !datos ? (
        <Esqueleto bloques={[80, 520]} />
      ) : (
        <Contenido key={perfil.id} datos={datos} citas={citas} />
      )}
    </Pagina>
  );
}
