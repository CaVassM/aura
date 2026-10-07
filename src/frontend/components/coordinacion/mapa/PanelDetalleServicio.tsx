"use client";

import { X } from "lucide-react";
import { getServicioDetalle } from "@/lib/api";
import { distritoLabel, fechaCorta, pct } from "@/lib/format";
import { ServicioDetalle } from "@/lib/types-coordinacion";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { textoDesvio } from "../resumen/DemandaPorTipo";
import { useApi } from "../useApi";
import NombreServicio, { NivelTag } from "../NombreServicio";
import { NIVEL_BG } from "../nivel";

/** Detalle de un servicio: datos de D6, ocupación, cupos por día y desencuentros recientes. */
export default function PanelDetalleServicio({
  serviceId,
  onClose,
}: {
  serviceId: string;
  onClose: () => void;
}) {
  const { data, error, cargando, reintentar } = useApi(
    () => getServicioDetalle(serviceId),
    [serviceId],
  );

  return (
    <aside className="h-fit rounded-xl2 border border-aura-teal/20 bg-white p-5 shadow-card xl:sticky xl:top-6">
      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !data ? (
        cargando && <EstadoCarga />
      ) : (
        <Contenido detalle={data} onClose={onClose} />
      )}
    </aside>
  );
}

function Contenido({
  detalle,
  onClose,
}: {
  detalle: ServicioDetalle;
  onClose: () => void;
}) {
  const s = detalle.servicio;
  const maxDia = Math.max(1, ...detalle.cupos_por_dia.map((d) => d.liberados));
  return (
    <>
      <div className="flex items-start justify-between gap-3">
        <div>
          <NombreServicio nombre={s.nombre} tipoLabel={s.tipo_label} apilado />
          <p className="mt-1.5 text-xs text-aura-gray">
            Distrito {distritoLabel(s.distrito)}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar detalle"
          className="rounded-lg p-1.5 text-aura-gray hover:bg-aura-bg hover:text-aura-navy"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <dl className="mt-5 space-y-3 text-sm">
        <div>
          <dt className="text-xs text-aura-gray">Dirección</dt>
          <dd className="mt-1 font-medium text-aura-navy">{s.direccion ?? "—"}</dd>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <dt className="text-xs text-aura-gray">Horario</dt>
            <dd className="mt-1 font-medium text-aura-navy">{s.horario_texto}</dd>
          </div>
          <div>
            <dt className="text-xs text-aura-gray">Canales</dt>
            <dd className="mt-1 font-medium text-aura-navy">
              {s.canales_label.join(", ")}
            </dd>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2 rounded-xl bg-aura-bg p-3 text-center">
          <Cifra etiqueta="Capacidad semanal" valor={s.capacidad_semanal} />
          <Cifra etiqueta="Liberados" valor={s.cupos_liberados} />
          <Cifra etiqueta="Ocupados" valor={s.cupos_ocupados} />
        </div>
        <div className="flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-aura-bg">
            <div
              className={`h-full rounded-full ${NIVEL_BG[s.nivel]}`}
              style={{ width: `${Math.min(100, s.ocupacion_pct)}%` }}
            />
          </div>
          <span className="font-bold text-aura-navy">{pct(s.ocupacion_pct)}</span>
          <NivelTag nivel={s.nivel} />
        </div>
      </dl>

      <div className="mt-5 border-t border-aura-border pt-4">
        <p className="text-xs font-bold uppercase tracking-wide text-aura-gray">
          Demanda de {s.tipo_label.toLowerCase()}
        </p>
        <dl className="mt-3 space-y-1.5 text-sm">
          <Fila etiqueta="Pedidos" valor={String(detalle.demanda_del_tipo.pedidos)} />
          <Fila etiqueta="Atendidos en su tipo" valor={String(detalle.demanda_del_tipo.atendidos_en_su_tipo)} />
          <Fila etiqueta="Con alternativa afín" valor={textoDesvio(detalle.demanda_del_tipo)} />
          <Fila etiqueta="Sin cupo" valor={String(detalle.demanda_del_tipo.sin_cupo)} />
          <Fila
            etiqueta="Recibidos de otros tipos"
            valor={
              detalle.recibidos_como_alternativa.cantidad === 0
                ? "Ninguno"
                : `${detalle.recibidos_como_alternativa.cantidad} ← ${detalle.recibidos_como_alternativa.origenes
                    .map((o) => `${o.tipo_label}: ${o.cantidad}`)
                    .join(", ")}`
            }
          />
        </dl>
        <p className="mt-2 text-[11px] text-aura-gray">
          Toda la demanda de este tipo de servicio, no solo la de este local.
        </p>
      </div>

      <div className="mt-5 border-t border-aura-border pt-4">
        <p className="text-xs font-bold uppercase tracking-wide text-aura-gray">
          Cupos liberados por día
        </p>
        <ul className="mt-3 space-y-1.5">
          {detalle.cupos_por_dia.map((d) => (
            <li
              key={d.fecha}
              className={`flex items-center gap-2 text-xs ${d.abierto ? "text-aura-navy" : "text-aura-gray-light"}`}
              title={d.abierto ? undefined : "Día ya pasado: no se puede reservar"}
            >
              <span className="w-16 shrink-0">
                {d.dia} {fechaCorta(d.fecha)}
              </span>
              <div className="relative h-2 flex-1 rounded-full bg-aura-bg">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-aura-teal-icon-bg"
                  style={{ width: `${(d.liberados / maxDia) * 100}%` }}
                />
                <div
                  className={`absolute inset-y-0 left-0 rounded-full ${d.abierto ? "bg-aura-teal" : "bg-aura-gray-light"}`}
                  style={{ width: `${(d.ocupados / maxDia) * 100}%` }}
                />
              </div>
              <span className="w-12 shrink-0 text-right">
                {d.ocupados}/{d.liberados}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-aura-gray">
          Ocupados / liberados. Los días en gris ya pasaron.
        </p>
      </div>

      <div className="mt-5 border-t border-aura-border pt-4">
        <p className="text-xs font-bold uppercase tracking-wide text-aura-gray">
          Desencuentros recientes
        </p>
        {detalle.desencuentros_recientes.length === 0 ? (
          <p className="mt-3 text-sm text-aura-gray">
            Sin desencuentros recientes para {s.tipo_label.toLowerCase()} en el
            distrito {distritoLabel(s.distrito)}.
          </p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm leading-5 text-aura-gray">
            {detalle.desencuentros_recientes.map((d) => (
              <li key={d.id} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-aura-chart-yellow" />
                <span>
                  {d.motivo_label} · {d.franja.dia} {d.franja.desde}–{d.franja.hasta}{" "}
                  · {d.grupo_label}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

function Fila({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-aura-gray">{etiqueta}</dt>
      <dd className="text-right font-semibold text-aura-navy">{valor}</dd>
    </div>
  );
}

function Cifra({ etiqueta, valor }: { etiqueta: string; valor: number }) {
  return (
    <div>
      <div className="text-[11px] text-aura-gray">{etiqueta}</div>
      <div className="mt-1 font-bold text-aura-navy">{valor}</div>
    </div>
  );
}
