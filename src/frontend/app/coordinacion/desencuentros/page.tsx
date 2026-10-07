"use client";

import { useState } from "react";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import { useApi } from "@/components/coordinacion/useApi";
import FiltrosDesencuentrosBarra from "@/components/coordinacion/desencuentros/FiltrosDesencuentros";
import HeatmapDiaHora from "@/components/coordinacion/desencuentros/HeatmapDiaHora";
import InsightCard from "@/components/coordinacion/desencuentros/InsightCard";
import TablaDesencuentros from "@/components/coordinacion/desencuentros/TablaDesencuentros";
import { EstadoCarga, EstadoError, EstadoVacio } from "@/components/ui/Estados";
import { getDesencuentros, getReglas, getServicios } from "@/lib/api";
import { FiltrosDesencuentros } from "@/lib/types-coordinacion";

const TAMANO = 8;

export default function DesencuentrosPage() {
  const [filtros, setFiltros] = useState<FiltrosDesencuentros>({});
  const [pagina, setPagina] = useState(1);

  // Opciones de los filtros: motivos y servicios ideales (reglas) y distritos (servicios de D6).
  const reglas = useApi(() => getReglas(), []);
  const servicios = useApi(() => getServicios(), []);
  const lista = useApi(
    () => getDesencuentros(filtros, pagina, TAMANO),
    [filtros.motivo, filtros.distrito, filtros.servicio_ideal, filtros.grupo, pagina],
  );

  const cambiarFiltros = (nuevos: FiltrosDesencuentros) => {
    setFiltros(nuevos);
    setPagina(1);
  };

  const error = lista.error ?? reglas.error ?? servicios.error;
  const reintentar = () => {
    lista.reintentar();
    reglas.reintentar();
    servicios.reintentar();
  };
  const datos = lista.data;

  return (
    <CoordinacionShell activeHref="/coordinacion/desencuentros">
      <div className="mx-auto max-w-6xl space-y-6 px-8 py-8">
        <div>
          <p className="text-xs font-bold tracking-wide text-aura-teal">
            DESENCUENTROS
          </p>
          <h2 className="mt-1.5 text-3xl font-bold text-aura-navy">
            Cuando la disponibilidad no coincide con lo que la persona necesita.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-aura-gray">
            Solicitudes que AURA no pudo atender con un cupo compatible. Sirven
            para decidir dónde abrir horarios; no se asignan manualmente.
          </p>
        </div>

        {error ? (
          <EstadoError error={error} onRetry={reintentar} />
        ) : !datos || !reglas.data || !servicios.data ? (
          <EstadoCarga />
        ) : (
          <>
            {datos.filtrados > 0 && <InsightCard insight={datos.insight} />}
            <FiltrosDesencuentrosBarra
              reglas={reglas.data}
              servicios={servicios.data.features}
              filtros={filtros}
              onChange={cambiarFiltros}
              filtrados={datos.filtrados}
            />

            {datos.filtrados === 0 ? (
              <div className="rounded-xl2 border border-dashed border-aura-border bg-white shadow-card">
                <EstadoVacio
                  titulo={
                    datos.total === 0
                      ? "Todavía no hay desencuentros"
                      : "Ningún desencuentro coincide con estos filtros"
                  }
                  descripcion={
                    datos.total === 0
                      ? "Cuando una solicitud no encuentre un cupo compatible, aparecerá aquí."
                      : `Hay ${datos.total} desencuentros registrados, pero ninguno cumple todos los filtros elegidos. Cambia o quita algún filtro para verlos.`
                  }
                  accion={
                    Object.values(filtros).some(Boolean) && (
                      <button
                        type="button"
                        onClick={() => cambiarFiltros({})}
                        className="rounded-xl border border-aura-teal px-4 py-2 text-sm font-semibold text-aura-teal hover:bg-aura-teal-pale"
                      >
                        Quitar filtros
                      </button>
                    )
                  }
                />
              </div>
            ) : (
              <>
                <HeatmapDiaHora heatmap={datos.heatmap} />
                <TablaDesencuentros
                  items={datos.items}
                  total={datos.filtrados}
                  pagina={datos.pagina}
                  paginas={datos.paginas}
                  tamano={TAMANO}
                  onPagina={setPagina}
                />
              </>
            )}
          </>
        )}
      </div>
    </CoordinacionShell>
  );
}
