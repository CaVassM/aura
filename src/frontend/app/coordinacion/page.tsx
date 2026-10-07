"use client";

import Link from "next/link";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import DemandaPorTipo from "@/components/coordinacion/resumen/DemandaPorTipo";
import GraficoOcupacion from "@/components/coordinacion/resumen/GraficoOcupacion";
import { useApi } from "@/components/coordinacion/useApi";
import StatCard from "@/components/ui/StatCard";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getResumen } from "@/lib/api";
import { fechaCorta, num, pct } from "@/lib/format";

export default function CoordinacionResumenPage() {
  const { data: resumen, error, cargando, reintentar } = useApi(
    () => getResumen(),
    [],
  );

  return (
    <CoordinacionShell activeHref="/coordinacion">
      <div className="mx-auto max-w-6xl space-y-6 px-8 py-8">
        <div>
          <p className="text-xs font-bold tracking-wide text-aura-teal">
            RESUMEN DE RED
          </p>
          <h2 className="mt-1.5 text-3xl font-bold text-aura-navy">
            Cupos liberados, vistos con claridad.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-aura-gray">
            AURA propone y reserva automáticamente según disponibilidad. Este
            espacio observa la red, sin asignar cupos manualmente.
          </p>
        </div>

        {error ? (
          <EstadoError error={error} onRetry={reintentar} />
        ) : !resumen ? (
          cargando && <EstadoCarga />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-5">
              <StatCard
                label="Citas agendadas en la semana"
                value={num(resumen.kpis.citas_agendadas, 0)}
                tagText={`Pedidos del ${fechaCorta(resumen.pedidos.desde)} al ${fechaCorta(resumen.pedidos.hasta)}`}
                tagVariant="green"
              />
              <StatCard
                label="Espera media"
                value={`${num(resumen.kpis.espera_media_dias)} días`}
                tagText={`Antes: ${num(resumen.kpis.espera_linea_base_dias, 0)} días (D2)`}
                tagVariant="purple"
              />
              <StatCard
                label="Ocupación de cupos liberados (%)"
                value={pct(resumen.kpis.ocupacion_pct)}
                tagText={`${num(resumen.kpis.cupos_ocupados, 0)} de ${num(resumen.kpis.cupos_liberados, 0)} cupos liberados`}
                tagVariant="yellow"
              />
              <StatCard
                label="Desencuentros registrados"
                value={num(resumen.kpis.desencuentros, 0)}
                tagText="Disponibilidad no compatible"
                tagVariant="red"
              />
              <StatCard
                label="Atendidos con alternativa afín"
                value={num(resumen.kpis.atendidos_alternativa, 0)}
                tagText="Pedidos desviados a otro tipo"
                tagVariant="purple"
              />
            </div>

            <GraficoOcupacion resumen={resumen} />

            <DemandaPorTipo demanda={resumen.demanda_por_tipo} />

            <div className="flex flex-col gap-4 rounded-xl2 border border-aura-teal/15 bg-aura-teal-pale p-5 shadow-card sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-bold text-aura-navy">Cobertura de la red</p>
                <p className="mt-1 text-sm leading-6 text-aura-gray">
                  {resumen.servicios.length} servicios en la red. Los datos
                  sirven para observar la red; las asignaciones siguen siendo
                  automáticas por AURA.
                </p>
              </div>
              <Link
                href="/coordinacion/mapa"
                className="shrink-0 rounded-xl border border-aura-teal px-4 py-2 text-center text-sm font-semibold text-aura-teal hover:bg-white"
              >
                Ver servicios en el mapa
              </Link>
            </div>
          </>
        )}
      </div>
    </CoordinacionShell>
  );
}
