"use client";

import { useEffect, useState } from "react";
import { Radio, Wifi, WifiOff } from "lucide-react";
import { useActividad } from "@/components/coordinacion/ActividadProvider";
import Barra from "@/components/coordinacion/Barra";
import NumeroAnimado from "@/components/coordinacion/NumeroAnimado";
import Seccion from "@/components/coordinacion/Seccion";
import { NIVEL_BG, NIVEL_INK } from "@/components/coordinacion/nivel";
import { detalleEvento, horaRegistro, META_EVENTO, ORIGEN_LABEL } from "@/components/coordinacion/en-vivo/evento";
import { bloqueFecha, distritoLabel, num } from "@/lib/format";
import { canalUi } from "@/lib/servicios-ui";
import { EventoActividad } from "@/lib/types-coordinacion";

const RECIENTE_MS = 6000;

function Contador({ titulo, valor, tinte, tinta }: { titulo: string; valor: number; tinte: string; tinta: string }) {
  return (
    <div className={`rounded-xl px-5 py-4 ${tinte}`}>
      <p className={`text-[11px] font-extrabold uppercase tracking-[0.14em] ${tinta}`}>{titulo}</p>
      <p className={`mt-1 text-4xl font-extrabold tracking-tight ${tinta}`}>
        <NumeroAnimado valor={valor} duracion={500} />
      </p>
    </div>
  );
}

function Fila({ e, reciente }: { e: EventoActividad; reciente: boolean }) {
  const m = META_EVENTO[e.tipo];
  const Icono = m.icono;
  const f = bloqueFecha(e.fecha_solicitud);
  return (
    <li
      className={`relative grid grid-cols-[auto_1fr] items-center gap-x-5 gap-y-2 py-4 pl-6 pr-5 animate-fade-in transition-colors duration-1000 lg:grid-cols-[7rem_9.5rem_1fr_14rem_7rem] ${
        reciente ? "bg-co-teal-tint/60" : "bg-transparent"
      }`}
    >
      <span className={`absolute inset-y-0 left-0 w-1.5 ${m.solido}`} aria-hidden="true" />

      <div>
        <p className="tabular text-sm font-extrabold text-co-navy">{horaRegistro(e.registrado_en)}</p>
        <p className="text-[11px] font-semibold text-co-ink">
          Demo · {f.numero} {f.mes}
        </p>
      </div>

      <span className={`inline-flex w-fit items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-bold ${m.tinte} ${m.tinta}`}>
        <Icono size={13} aria-hidden="true" />
        {m.label}
      </span>

      <div className="min-w-0 col-span-2 lg:col-span-1">
        <p className="truncate text-sm font-bold text-co-navy">
          {e.servicio ? (
            <>
              {e.servicio.nombre}
              <span className="text-xs font-semibold text-co-teal"> · {e.servicio.tipo_label}</span>
            </>
          ) : e.desencuentro ? (
            <>
              Sin cupo de {e.desencuentro.servicio_ideal_label}
              <span className="text-xs font-semibold text-co-amber-ink"> · {distritoLabel(e.desencuentro.distrito)}</span>
            </>
          ) : (
            <>Lote {e.lote?.id}</>
          )}
        </p>
        <p className="truncate text-xs font-semibold text-co-ink">{detalleEvento(e)}</p>
        <p className="mt-0.5 text-[11px] font-semibold text-co-ink/80">
          {e.estudiante_id ?? "Sistema"}
          <span className="lg:hidden"> · {ORIGEN_LABEL[e.origen]}</span>
          {e.cita?.es_alternativa && <span className="text-co-amber-ink"> · servicio alternativo</span>}
          {e.cita && e.cita.dias_espera != null && <span> · espera {e.cita.dias_espera} d</span>}
        </p>
      </div>

      <div className="col-span-2 lg:col-span-1">
        {e.ocupacion ? (
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5 text-xs font-bold">
              <span className="flex items-center gap-1.5 text-co-ink">
                Ocupación
                {e.ocupacion.en_lote && (
                  <span className="rounded bg-co-coral px-1.5 py-0.5 text-[10px] font-extrabold uppercase leading-none tracking-wider text-white">
                    en lote
                  </span>
                )}
              </span>
              <span className={`tabular ${NIVEL_INK[e.ocupacion.nivel]}`}>
                {num(e.ocupacion.antes_pct)} % → {num(e.ocupacion.pct)} %
              </span>
            </div>
            <div className="mt-1.5">
              <Barra pct={e.ocupacion.pct} color={NIVEL_BG[e.ocupacion.nivel]} alto="h-2" etiqueta={`Ocupación ${num(e.ocupacion.pct)} %`} />
            </div>
            <p className="mt-1 tabular text-[11px] font-semibold text-co-ink/80">
              {e.ocupacion.reservados} de {e.ocupacion.liberados} cupos liberados
            </p>
          </>
        ) : e.lote ? (
          <>
            <div className="flex items-baseline justify-between text-xs font-bold">
              <span className="text-co-ink">{e.lote.resultado ? "Resultado" : "Solicitudes"}</span>
              <span className="tabular text-co-teal-dark">
                {e.lote.resultado ? `${e.lote.resultado.asignados} de ${e.lote.solicitudes}` : `${e.lote.solicitudes} / ${e.lote.tamano_maximo}`}
              </span>
            </div>
            <div className="mt-1.5">
              <Barra
                pct={e.lote.resultado ? (100 * e.lote.resultado.asignados) / Math.max(1, e.lote.solicitudes) : (100 * e.lote.solicitudes) / e.lote.tamano_maximo}
                color="bg-co-teal"
                alto="h-2"
              />
            </div>
          </>
        ) : e.desencuentro ? (
          <p className="text-xs font-semibold text-co-ink">
            Aceptaba: {e.desencuentro.canales.map((c) => canalUi(c).label).join(", ")} · {e.desencuentro.grupo_label}
          </p>
        ) : null}
      </div>

      <div className="hidden justify-self-end lg:block">
        <span className="rounded-md bg-co-bg px-2 py-1 text-[11px] font-bold text-co-ink">{ORIGEN_LABEL[e.origen]}</span>
      </div>
    </li>
  );
}

export default function EnVivoPage() {
  const { eventos, conectado } = useActividad();
  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const reservadas = eventos.filter((e) => e.tipo === "cita_reservada").length;
  const canceladas = eventos.filter((e) => e.tipo === "cita_cancelada").length;
  const desencuentros = eventos.filter((e) => e.tipo === "desencuentro").length;
  const lotes = eventos.filter((e) => e.tipo === "lote_resuelto").length;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">En vivo</h1>
          <p className="mt-1 max-w-2xl text-sm font-medium leading-relaxed text-co-ink">
            Cada cita que un estudiante reserva o cancela, cada solicitud sin cupo y cada novedad del modo lote aparecen
            aquí al instante. Solo se
            registra lo nuevo: las citas que ya vienen cargadas en la demo no figuran en este registro.
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-bold ${
            conectado ? "bg-co-sage-tint text-co-sage-ink" : "bg-co-amber-tint text-co-amber-ink"
          }`}
        >
          {conectado ? <Wifi size={15} aria-hidden="true" /> : <WifiOff size={15} aria-hidden="true" />}
          {conectado ? "Conectado en tiempo real" : "Reconectando…"}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Contador titulo="Citas nuevas" valor={reservadas} tinte="bg-co-sage-tint" tinta="text-co-sage-ink" />
        <Contador titulo="Canceladas" valor={canceladas} tinte="bg-co-coral-tint" tinta="text-co-coral-ink" />
        <Contador titulo="Desencuentros" valor={desencuentros} tinte="bg-co-amber-tint" tinta="text-co-amber-ink" />
        <Contador titulo="Lotes resueltos" valor={lotes} tinte="bg-co-teal-tint" tinta="text-co-teal-dark" />
      </div>

      <Seccion titulo="Registro de citas nuevas" acento="bg-co-teal">
        {eventos.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-co-line bg-co-paper px-8 py-16 text-center">
            <span className="relative flex h-14 w-14 items-center justify-center rounded-full bg-co-teal-tint text-co-teal">
              <span className="halo-pulso absolute inset-0 rounded-full bg-co-teal animate-halo" aria-hidden="true" />
              <Radio size={24} aria-hidden="true" />
            </span>
            <p className="text-base font-extrabold text-co-navy">Esperando actividad…</p>
            <p className="max-w-md text-sm text-co-ink">
              Cuando un estudiante agende desde el campus (<span className="font-bold">/campus/chat</span>), aparecerá
              aquí en el mismo instante. Abre esa pantalla en otra ventana para verlo.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-co-line overflow-hidden rounded-2xl border border-co-line bg-co-paper shadow-card">
            {eventos.map((e) => (
              <Fila key={e.id} e={e} reciente={ahora - Date.parse(e.registrado_en) < RECIENTE_MS} />
            ))}
          </ul>
        )}
      </Seccion>
    </div>
  );
}
