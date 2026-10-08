"use client";

import { useState } from "react";
import { useApi } from "@/components/coordinacion/useApi";
import { ConInfo } from "@/components/coordinacion/InfoTip";
import NumeroAnimado from "@/components/coordinacion/NumeroAnimado";
import Seccion from "@/components/coordinacion/Seccion";
import FiltrosDesencuentrosBarra from "@/components/coordinacion/desencuentros/FiltrosDesencuentros";
import InsightCard from "@/components/coordinacion/desencuentros/InsightCard";
import MatrizDistritoServicio from "@/components/coordinacion/desencuentros/MatrizDistritoServicio";
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
  const franja = datos?.franja_principal;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <h1 className="text-3xl font-extrabold tracking-tight text-co-navy">Desencuentros</h1>

      {error ? (
        <EstadoError error={error} onRetry={reintentar} />
      ) : !datos || !reglas.data || !servicios.data ? (
        <EstadoCarga />
      ) : (
        <>
          {franja && (
            <p className="flex flex-wrap items-center text-base font-medium leading-snug text-co-navy">
              <span className="mr-1.5 font-extrabold text-co-coral-ink">
                <NumeroAnimado valor={franja.porcentaje} decimales={franja.porcentaje % 1 ? 1 : 0} sufijo=" %" />
              </span>
              piden {franja.texto}
              <ConInfo termino="franja">{""}</ConInfo>
            </p>
          )}
          {datos.total > 0 && (
            <InsightCard
              insight={datos.insight}
              filtro={datos.filtrados > 0 ? datos.insight_filtro : null}
            />
          )}

          <FiltrosDesencuentrosBarra
            reglas={reglas.data}
            servicios={servicios.data.features}
            filtros={filtros}
            onChange={cambiarFiltros}
            filtrados={datos.filtrados}
          />

          {datos.filtrados === 0 ? (
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
                    className="co-foco rounded-md border border-co-teal px-4 py-2 text-sm font-bold text-co-teal hover:bg-co-teal-tint"
                  >
                    Quitar filtros
                  </button>
                )
              }
            />
          ) : (
            <>
              <Seccion titulo="Dónde se concentran: distrito × servicio ideal" acento="bg-co-coral">
                <MatrizDistritoServicio
                  matriz={datos.matriz_distrito_servicio}
                  distritoActivo={filtros.distrito}
                  servicioActivo={filtros.servicio_ideal}
                  onSeleccion={(distrito, servicio_ideal) =>
                    cambiarFiltros({ ...filtros, distrito, servicio_ideal })
                  }
                />
              </Seccion>
              <Seccion titulo="Pedidos sin cupo" acento="bg-co-teal">
                <TablaDesencuentros
                  items={datos.items}
                  total={datos.filtrados}
                  pagina={datos.pagina}
                  paginas={datos.paginas}
                  tamano={TAMANO}
                  onPagina={setPagina}
                />
              </Seccion>
            </>
          )}
        </>
      )}
    </div>
  );
}
