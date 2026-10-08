"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { getServicioDetalle } from "@/lib/api";
import { distritoLabel, fechaCorta } from "@/lib/format";
import { ServicioDetalle } from "@/lib/types-coordinacion";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import Barra from "./Barra";
import { useDemo } from "./DemoProvider";
import EmbudoCupos from "./EmbudoCupos";
import InfoTip from "./InfoTip";
import NombreServicio, { NivelTag } from "./NombreServicio";
import { NIVEL_BG, NIVEL_INK } from "./nivel";
import NumeroAnimado from "./NumeroAnimado";
import Seccion from "./Seccion";
import { useApi } from "./useApi";

/**
 * Panel lateral con el detalle de un servicio (se abre desde el mapa y desde la tabla de
 * Servicios): datos de D6, embudo de cupos, cupos por día y desencuentros recientes.
 *
 * En pantallas anchas (xl) es una columna pegada al borde derecho DENTRO del diseño de la página:
 * empuja el contenido (el mapa se reajusta) y no tapa la cabecera. En pantallas estrechas se
 * superpone. No bloquea la pantalla; Esc lo cierra.
 */
export default function DrawerServicio({
  serviceId,
  onClose,
}: {
  serviceId: string;
  onClose: () => void;
}) {
  const [cerrando, setCerrando] = useState(false);
  const cerrar = useRef(() => {});
  cerrar.current = () => {
    setCerrando(true);
    window.setTimeout(onClose, 200);
  };

  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => e.key === "Escape" && cerrar.current();
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, []);

  const { data, error, cargando, reintentar } = useApi(
    () => getServicioDetalle(serviceId),
    [serviceId],
  );

  return (
    <aside
      role="dialog"
      aria-label="Detalle del servicio"
      className={`fixed inset-y-0 right-0 z-40 w-full max-w-[28rem] overflow-y-auto border-l border-co-line bg-co-paper shadow-drawer xl:sticky xl:inset-auto xl:top-4 xl:z-auto xl:h-[calc(100vh-2rem)] xl:self-start xl:rounded-lg xl:border xl:shadow-card ${cerrando ? "animate-slide-out-right" : "animate-slide-in-right"}`}
    >
      <button
        type="button"
        onClick={() => cerrar.current()}
        aria-label="Cerrar detalle del servicio"
        className="co-foco absolute right-3 top-3 rounded-md p-1.5 text-co-ink hover:bg-co-teal-tint hover:text-co-navy"
      >
        <X className="h-5 w-5" />
      </button>
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !data ? (
        cargando && <EstadoCarga />
      ) : (
        <Contenido detalle={data} />
      )}
    </aside>
  );
}

function Dato({ etiqueta, children }: { etiqueta: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-bold text-co-navy">{etiqueta}</dt>
      <dd className="mt-0.5 text-sm font-medium text-co-ink">{children}</dd>
    </div>
  );
}

function Contenido({ detalle }: { detalle: ServicioDetalle }) {
  const { estado } = useDemo();
  const semanas = estado ? `${estado.agenda_abierta_semanas} semanas` : "agenda abierta";
  const s = detalle.servicio;
  const maxDia = Math.max(1, ...detalle.cupos_por_dia.map((d) => d.liberados));
  return (
    <div className="space-y-7 px-6 pb-10 pt-6">
      <header className="pr-10">
        <NombreServicio nombre={s.nombre} tipoLabel={s.tipo_label} apilado />
        <p className="mt-1 text-xs font-semibold text-co-ink">Distrito {distritoLabel(s.distrito)}</p>
      </header>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
        <Dato etiqueta="Horario">{s.horario_texto}</Dato>
        <Dato etiqueta="Canales">{s.canales_label.join(", ")}</Dato>
        <Dato etiqueta="Capacidad semanal (D6)">
          <span className="inline-flex items-center tabular font-bold text-co-navy">
            {s.capacidad_semanal}
            <InfoTip termino="capacidad_semanal" />
          </span>
        </Dato>
        {s.direccion && <Dato etiqueta="Dirección">{s.direccion}</Dato>}
      </dl>

      <Seccion titulo={`Cupos · ${semanas}`} acento="bg-co-teal">
        <EmbudoCupos
          columnas={2}
          datos={{
            capacidad: s.capacidad_agenda_abierta,
            libres: s.libres_agenda_abierta,
            liberados: s.cupos_liberados,
            reservados: s.cupos_reservados,
          }}
        />
        <div className="mt-1 flex items-center gap-3">
          <div className="flex-1">
            <Barra pct={s.ocupacion_pct} color={NIVEL_BG[s.nivel]} alto="h-2.5" retraso={300} />
          </div>
          <span className={`text-lg font-extrabold ${NIVEL_INK[s.nivel]}`}>
            <NumeroAnimado valor={s.ocupacion_pct} decimales={1} sufijo="%" />
          </span>
          <NivelTag nivel={s.nivel} />
        </div>
      </Seccion>

      <Seccion titulo="Liberados por día" acento="bg-co-amber">
        <ul className="space-y-1.5">
          {detalle.cupos_por_dia.map((d, i) => (
            <li
              key={d.fecha}
              className={`grid grid-cols-[4.75rem_1fr_3.25rem] items-center gap-2 text-xs ${d.abierto ? "text-co-navy" : "text-co-ink"}`}
              title={d.abierto ? undefined : "Día ya pasado: no se puede reservar"}
            >
              <span className="font-semibold">
                {d.dia} {fechaCorta(d.fecha)}
              </span>
              <div className="relative h-2 overflow-hidden rounded-full bg-co-line/70">
                <div
                  className="absolute inset-y-0 left-0 origin-left animate-grow-x rounded-full bg-co-teal/35"
                  style={{ width: `${(d.liberados / maxDia) * 100}%`, animationDelay: `${i * 40}ms` }}
                />
                <div
                  className={`absolute inset-y-0 left-0 origin-left animate-grow-x rounded-full ${d.abierto ? "bg-co-teal" : "bg-co-ink/50"}`}
                  style={{ width: `${(d.reservados / maxDia) * 100}%`, animationDelay: `${i * 40 + 120}ms` }}
                />
              </div>
              <span className="tabular text-right font-bold">
                {d.reservados}/{d.liberados}
              </span>
            </li>
          ))}
        </ul>
        <p className="text-[11px] font-medium text-co-ink">
          Reservados / liberados. Los días en gris ya pasaron.
        </p>
      </Seccion>

      <Seccion titulo="Desencuentros recientes" acento="bg-co-coral">
        {detalle.desencuentros_recientes.length === 0 ? (
          <p className="text-sm font-medium text-co-ink">
            Sin desencuentros recientes para {s.tipo_label.toLowerCase()} en el distrito{" "}
            {distritoLabel(s.distrito)}.
          </p>
        ) : (
          <ul className="space-y-2 text-sm leading-5 text-co-navy">
            {detalle.desencuentros_recientes.map((d) => (
              <li key={d.id} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-co-coral" />
                <span>
                  <span className="font-bold">{d.motivo_label}</span> · {d.franja.dia}{" "}
                  {d.franja.desde}–{d.franja.hasta} · {d.grupo_label}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Seccion>
    </div>
  );
}
