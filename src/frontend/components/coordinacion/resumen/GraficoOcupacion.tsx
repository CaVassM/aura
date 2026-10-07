import { Resumen } from "@/lib/types-coordinacion";
import { pct, rangoFechas } from "@/lib/format";
import LeyendaNiveles from "../LeyendaNiveles";
import { NIVEL_BG } from "../nivel";

/**
 * Barras horizontales de ocupación por servicio. El ancho y el nivel (color) vienen del backend;
 * se dibujan con divs (ancho en línea), sin librerías de gráficos.
 */
export default function GraficoOcupacion({ resumen }: { resumen: Resumen }) {
  const { agenda_abierta, servicios } = resumen;
  return (
    <div className="rounded-xl2 border border-aura-border bg-white p-6 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-base font-bold text-aura-navy">
            Ocupación de cupos liberados
          </p>
          <p className="text-sm text-aura-gray">
            Por servicio · agenda abierta{" "}
            {rangoFechas(agenda_abierta.desde, agenda_abierta.hasta)}
          </p>
        </div>
        <LeyendaNiveles />
      </div>

      <ul className="mt-6 space-y-3 border-t border-aura-border pt-5">
        {servicios.map((s) => (
          <li
            key={s.service_id}
            className="flex items-center gap-4 text-sm"
            title={`${s.cupos_ocupados} de ${s.cupos_liberados} cupos liberados ocupados`}
          >
            <span className="w-56 shrink-0 text-right leading-tight">
              <span className="block text-aura-navy">{s.nombre}</span>
              <span className="block text-xs text-aura-gray">{s.tipo_label}</span>
            </span>
            <div
              className="h-3 flex-1 overflow-hidden rounded-full bg-aura-bg"
              role="img"
              aria-label={`${s.nombre}, ${s.tipo_label}: ${pct(s.ocupacion_pct)} de ocupación`}
            >
              <div
                className={`h-full rounded-full ${NIVEL_BG[s.nivel]}`}
                style={{ width: `${Math.min(100, Math.max(0, s.ocupacion_pct))}%` }}
              />
            </div>
            <span className="w-12 shrink-0 text-xs text-aura-gray">
              {pct(s.ocupacion_pct)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
