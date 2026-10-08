"use client";

import { useEffect, useState } from "react";
import DrawerServicio from "@/components/coordinacion/DrawerServicio";
import { useApi } from "@/components/coordinacion/useApi";
import FiltrosMapa from "@/components/coordinacion/mapa/FiltrosMapa";
import MapaCiudad from "@/components/coordinacion/mapa/MapaCiudad";
import { EstadoCarga, EstadoError } from "@/components/ui/Estados";
import { getServicios } from "@/lib/api";
import { FiltrosServicios } from "@/lib/types-coordinacion";

export default function MapaPage() {
  const [filtros, setFiltros] = useState<FiltrosServicios>({});
  const [seleccionado, setSeleccionado] = useState<string | null>(null);

  // Todos los servicios (opciones del filtro y distritos del mapa) y los que cumplen los filtros.
  const todos = useApi(() => getServicios(), []);
  const filtrados = useApi(() => getServicios(filtros), [filtros.tipo, filtros.solo_alta_demanda]);

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
    <div className="mx-auto max-w-[100rem] space-y-5">
      <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Mapa de servicios</h1>

      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !todos.data || !filtrados.data ? (
        <EstadoCarga />
      ) : (
        // Con un servicio abierto, en pantallas anchas el panel es una columna y el mapa se reajusta.
        <div className={seleccionado ? "gap-6 xl:grid xl:grid-cols-[minmax(0,1fr)_28rem]" : ""}>
          <div className="min-w-0 space-y-5">
            <FiltrosMapa todos={todos.data.features} filtros={filtros} onChange={setFiltros} />
            <MapaCiudad
              todos={todos.data.features}
              visibles={visibles}
              seleccionadoId={seleccionado}
              onSelect={setSeleccionado}
              onLimpiarFiltros={() => setFiltros({})}
            />
          </div>
          {seleccionado && (
            <DrawerServicio serviceId={seleccionado} onClose={() => setSeleccionado(null)} />
          )}
        </div>
      )}
    </div>
  );
}
