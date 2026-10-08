"use client";

import { distritoLabel, num } from "@/lib/format";
import { MatrizDistritoServicio as Matriz } from "@/lib/types-coordinacion";
import InfoTip from "../InfoTip";

/** Color de una celda: intensidad coral según el conteo (el texto siempre en navy, AA). */
function fondo(valor: number, maximo: number): string | undefined {
  if (valor === 0 || maximo === 0) return undefined;
  return `rgba(217, 87, 61, ${(0.1 + 0.55 * (valor / maximo)).toFixed(2)})`;
}

/**
 * Matriz de desencuentros: distrito (filas) × servicio ideal (columnas), con totales. Respeta los
 * filtros activos. Un clic en una celda filtra por ese distrito y servicio; otro clic quita el filtro.
 */
export default function MatrizDistritoServicio({
  matriz,
  distritoActivo,
  servicioActivo,
  onSeleccion,
}: {
  matriz: Matriz;
  distritoActivo?: string;
  servicioActivo?: string;
  /** `undefined` en un eje = sin filtro en ese eje. */
  onSeleccion: (distrito: string | undefined, servicio: string | undefined) => void;
}) {
  const maximo = Math.max(0, ...matriz.celdas.flat());

  const celdaActiva = (d: string, t: string) => distritoActivo === d && servicioActivo === t;
  const alternar = (d: string | undefined, t: string | undefined) =>
    onSeleccion(
      d === distritoActivo && t === servicioActivo ? undefined : d,
      d === distritoActivo && t === servicioActivo ? undefined : t,
    );

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] border-separate border-spacing-1 text-center text-sm">
        <thead>
          <tr>
            <th className="w-32 text-left text-xs font-extrabold text-co-navy">Distrito</th>
            {matriz.servicios.map((s, j) => (
              <th key={s.tipo} scope="col" className="px-1 pb-1">
                <button
                  type="button"
                  onClick={() => onSeleccion(distritoActivo, servicioActivo === s.tipo ? undefined : s.tipo)}
                  className={`co-foco rounded px-1.5 py-1 text-xs font-extrabold ${servicioActivo === s.tipo ? "bg-co-teal text-white" : "text-co-navy hover:bg-co-teal-tint"}`}
                >
                  {s.label}
                </button>
                {j === 0 && <InfoTip termino="servicio_ideal" />}
              </th>
            ))}
            <th scope="col" className="px-1 pb-1 text-xs font-extrabold text-co-navy">
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {matriz.distritos.map((d, i) => (
            <tr key={d}>
              <th scope="row" className="text-left">
                <button
                  type="button"
                  onClick={() => onSeleccion(distritoActivo === d ? undefined : d, servicioActivo)}
                  className={`co-foco rounded px-1.5 py-1 text-left text-sm font-bold ${distritoActivo === d ? "bg-co-teal text-white" : "text-co-navy hover:bg-co-teal-tint"}`}
                >
                  {distritoLabel(d)}
                </button>
              </th>
              {matriz.celdas[i].map((valor, j) => {
                const tipo = matriz.servicios[j].tipo;
                const activa = celdaActiva(d, tipo);
                return (
                  <td key={tipo} className="p-0">
                    <button
                      type="button"
                      disabled={valor === 0 && !activa}
                      onClick={() => alternar(d, tipo)}
                      aria-pressed={activa}
                      aria-label={`${distritoLabel(d)}, ${matriz.servicios[j].label}: ${valor} desencuentros`}
                      style={{
                        backgroundColor: fondo(valor, maximo),
                        animationDelay: `${(i * matriz.servicios.length + j) * 35}ms`,
                      }}
                      className={`co-foco tabular h-12 w-full animate-fade-only rounded-md text-base font-extrabold transition-[background-color,box-shadow] duration-500 ${
                        valor === 0 ? "bg-co-line/40 text-co-ink/60" : "text-co-navy hover:ring-2 hover:ring-co-teal/60"
                      } ${activa ? "ring-2 ring-co-teal ring-offset-1" : ""}`}
                    >
                      {valor === 0 ? "·" : num(valor, 0)}
                    </button>
                  </td>
                );
              })}
              <td className="tabular px-2 text-base font-extrabold text-co-navy">{num(matriz.total_filas[i], 0)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" className="pt-1 text-left text-xs font-extrabold text-co-navy">
              Total
            </th>
            {matriz.total_columnas.map((t, j) => (
              <td key={matriz.servicios[j].tipo} className="tabular pt-1 text-base font-extrabold text-co-navy">
                {num(t, 0)}
              </td>
            ))}
            <td className="tabular pt-1 text-base font-extrabold text-co-coral-ink">{num(matriz.total, 0)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
