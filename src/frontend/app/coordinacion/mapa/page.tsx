"use client";

import { useEffect, useState } from "react";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import { useApi } from "@/components/coordinacion/useApi";
import FiltrosMapa from "@/components/coordinacion/mapa/FiltrosMapa";
import MapaCiudad from "@/components/coordinacion/mapa/MapaCiudad";
import PanelDetalleServicio from "@/components/coordinacion/mapa/PanelDetalleServicio";
import TablaServicios from "@/components/coordinacion/mapa/TablaServicios";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getServicios } from "@/lib/api";
import { FiltrosServicios } from "@/lib/types-coordinacion";

export default function MapaPage() {
  const [filtros, setFiltros] = useState<FiltrosServicios>({});
  const [seleccionado, setSeleccionado] = useState<string | null>(null);

  // Todos los servicios (opciones de los filtros y distritos del mapa) y los que cumplen los filtros.
  const todos = useApi(() => getServicios(), []);
  const filtrados = useApi(
    () => getServicios(filtros),
    [filtros.tipo, filtros.canal, filtros.solo_alta_demanda],
  );

  const visibles = filtrados.data?.features ?? [];
  useEffect(() => {
    if (seleccionado && filtrados.data && !visibles.some((f) => f.id === seleccionado))
      setSeleccionado(null);
  }, [filtrados.data, seleccionado, visibles]);

  const error = todos.error ?? filtrados.error;
  const reintentar = () => {
    todos.reintentar();
    filtrados.reintentar();
  };

  return (
    <CoordinacionShell activeHref="/coordinacion/mapa">
      <div className="mx-auto max-w-6xl space-y-6 px-8 py-8">
        <div>
          <p className="text-xs font-bold tracking-wide text-aura-teal">
            MAPA DE SERVICIOS
          </p>
          <h2 className="mt-1.5 text-3xl font-bold text-aura-navy">
            Dónde está la demanda, servicio por servicio.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-aura-gray">
            Mapa ilustrativo: las posiciones respetan la ubicación relativa de
            los servicios (datos sintéticos). El color indica el nivel de
            ocupación de sus cupos liberados.
          </p>
        </div>

        {error ? (
          <EstadoError error={error} onRetry={reintentar} />
        ) : !todos.data || !filtrados.data ? (
          <EstadoCarga />
        ) : (
          <>
            <FiltrosMapa
              todos={todos.data.features}
              filtros={filtros}
              onChange={setFiltros}
            />
            <div
              className={`grid gap-5 ${seleccionado ? "xl:grid-cols-[minmax(0,1fr)_22rem]" : ""}`}
            >
              <div className="overflow-hidden rounded-xl2 border border-aura-border bg-white shadow-card">
                <MapaCiudad
                  todos={todos.data.features}
                  visibles={visibles}
                  seleccionadoId={seleccionado}
                  onSelect={setSeleccionado}
                  onLimpiarFiltros={() => setFiltros({})}
                />
              </div>
              {seleccionado && (
                <PanelDetalleServicio
                  serviceId={seleccionado}
                  onClose={() => setSeleccionado(null)}
                />
              )}
            </div>
            {visibles.length > 0 && (
              <TablaServicios
                servicios={visibles}
                seleccionadoId={seleccionado}
                onSelect={setSeleccionado}
              />
            )}
          </>
        )}
      </div>
    </CoordinacionShell>
  );
}
