"use client";

import { useApi } from "@/components/coordinacion/useApi";
import { useDemo } from "@/components/coordinacion/DemoProvider";
import EmbudoCupos from "@/components/coordinacion/EmbudoCupos";
import { ConInfo } from "@/components/coordinacion/InfoTip";
import Seccion from "@/components/coordinacion/Seccion";
import BandaKpis from "@/components/coordinacion/resumen/BandaKpis";
import DemandaPorTipo from "@/components/coordinacion/resumen/DemandaPorTipo";
import EsperaHeroe from "@/components/coordinacion/resumen/EsperaHeroe";
import GraficoOcupacion, { LeyendaNiveles } from "@/components/coordinacion/resumen/GraficoOcupacion";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getResumen } from "@/lib/api";

export default function CoordinacionResumenPage() {
  const { estado } = useDemo();
  const { data: resumen, error, cargando, reintentar } = useApi(() => getResumen(), []);
  const semanas = estado ? `${estado.agenda_abierta_semanas} semanas` : "agenda abierta";

  return (
    <div className="mx-auto max-w-7xl space-y-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Resumen de la red</h1>

      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !resumen ? (
        cargando && <EstadoCarga />
      ) : (
        <>
          <div className="grid items-stretch gap-8 lg:grid-cols-[minmax(0,4fr)_minmax(0,8fr)]">
            <EsperaHeroe kpis={resumen.kpis} />
            <div className="flex items-center border-y border-co-line">
              <div className="w-full">
                <BandaKpis resumen={resumen} />
              </div>
            </div>
          </div>

          <Seccion titulo={`Cupos de la red · ${semanas}`} acento="bg-co-teal">
            <EmbudoCupos
              datos={{
                capacidad: resumen.kpis.capacidad_agenda_abierta,
                libres: resumen.kpis.libres_agenda_abierta,
                liberados: resumen.kpis.cupos_liberados,
                reservados: resumen.kpis.cupos_reservados,
              }}
            />
          </Seccion>

          <Seccion
            titulo={`Ocupación por servicio · ${semanas}`}
            acento="bg-co-amber"
            info={<InfoPlano />}
            derecha={<LeyendaNiveles />}
          >
            <GraficoOcupacion resumen={resumen} />
          </Seccion>

          <Seccion titulo="Demanda real por tipo de servicio" acento="bg-co-coral">
            <DemandaPorTipo demanda={resumen.demanda_por_tipo} />
          </Seccion>
        </>
      )}
    </div>
  );
}

/** ⓘ de «Ocupación de cupos liberados» junto al título de la sección. */
function InfoPlano() {
  return <ConInfo termino="ocupacion">{""}</ConInfo>;
}
