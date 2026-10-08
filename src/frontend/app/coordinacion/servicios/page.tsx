"use client";

import { useState } from "react";
import DrawerServicio from "@/components/coordinacion/DrawerServicio";
import FiltroSelect from "@/components/coordinacion/FiltroSelect";
import { NIVEL_LABEL, NIVELES } from "@/components/coordinacion/nivel";
import TablaServicios from "@/components/coordinacion/servicios/TablaServicios";
import { useApi } from "@/components/coordinacion/useApi";
import { EstadoCarga, EstadoError, EstadoVacio } from "@/components/ui/Estados";
import { getServicios } from "@/lib/api";
import { distritoLabel } from "@/lib/format";
import { FiltrosServicios } from "@/lib/types-coordinacion";

export default function ServiciosPage() {
  const [filtros, setFiltros] = useState<FiltrosServicios>({});
  const [orden, setOrden] = useState<"asc" | "desc">("desc");
  const [seleccionado, setSeleccionado] = useState<string | null>(null);

  // Todos (opciones de los filtros) y los que cumplen los filtros (el backend filtra).
  const todos = useApi(() => getServicios(), []);
  const lista = useApi(
    () => getServicios(filtros),
    [filtros.tipo, filtros.distrito, filtros.nivel],
  );

  const error = todos.error ?? lista.error;
  const reintentar = () => {
    todos.reintentar();
    lista.reintentar();
  };

  const tipos = new Map<string, string>();
  const distritos = new Set<string>();
  todos.data?.features.forEach(({ properties: p }) => {
    tipos.set(p.tipo, p.tipo_label);
    distritos.add(p.distrito);
  });
  const activos = Boolean(filtros.tipo || filtros.distrito || filtros.nivel);

  return (
    <div className="mx-auto max-w-[100rem] space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Servicios</h1>

      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !todos.data || !lista.data ? (
        <EstadoCarga />
      ) : (
        // Con un servicio abierto, en pantallas anchas el panel es una columna y la tabla se reajusta.
        <div className={seleccionado ? "gap-6 xl:grid xl:grid-cols-[minmax(0,1fr)_28rem]" : ""}>
          <div className="min-w-0 space-y-6">
            <div className="flex flex-wrap items-end gap-x-5 gap-y-3">
              <FiltroSelect
                etiqueta="Tipo de servicio"
                valor={filtros.tipo ?? ""}
                opciones={[...tipos].map(([valor, label]) => ({ valor, label }))}
                onChange={(tipo) => setFiltros({ ...filtros, tipo: tipo || undefined })}
              />
              <FiltroSelect
                etiqueta="Distrito"
                valor={filtros.distrito ?? ""}
                opciones={[...distritos].sort().map((d) => ({ valor: d, label: distritoLabel(d) }))}
                onChange={(distrito) => setFiltros({ ...filtros, distrito: distrito || undefined })}
              />
              <FiltroSelect
                etiqueta="Nivel"
                termino="nivel"
                valor={filtros.nivel ?? ""}
                opciones={NIVELES.map((n) => ({ valor: n, label: NIVEL_LABEL[n] }))}
                onChange={(nivel) => setFiltros({ ...filtros, nivel: nivel || undefined })}
              />
              <button
                type="button"
                onClick={() => setFiltros({})}
                disabled={!activos}
                className="co-foco pb-2 text-sm font-bold text-co-teal disabled:cursor-default disabled:text-co-ink/50"
              >
                Limpiar
              </button>
            </div>

            {lista.data.features.length === 0 ? (
              <EstadoVacio
                titulo="Ningún servicio coincide con los filtros"
                descripcion="Prueba con otro tipo, distrito o nivel de ocupación."
                accion={
                  <button
                    type="button"
                    onClick={() => setFiltros({})}
                    className="co-foco rounded-md border border-co-teal px-4 py-2 text-sm font-bold text-co-teal hover:bg-co-teal-tint"
                  >
                    Limpiar filtros
                  </button>
                }
              />
            ) : (
              <TablaServicios
                servicios={lista.data.features}
                seleccionadoId={seleccionado}
                orden={orden}
                onOrden={() => setOrden(orden === "desc" ? "asc" : "desc")}
                onSelect={setSeleccionado}
              />
            )}
          </div>
          {seleccionado && (
            <DrawerServicio serviceId={seleccionado} onClose={() => setSeleccionado(null)} />
          )}
        </div>
      )}
    </div>
  );
}
