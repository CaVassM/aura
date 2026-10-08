"use client";

import { Resumen } from "@/lib/types-coordinacion";
import { pct } from "@/lib/format";
import Barra from "../Barra";
import InfoTip from "../InfoTip";
import { NIVEL_BG, NIVEL_INK, NIVEL_LABEL, NIVELES } from "../nivel";
import NumeroAnimado from "../NumeroAnimado";
import { useDemo } from "../DemoProvider";
import { num } from "@/lib/format";

/** Leyenda baja / media / alta con los umbrales que define el backend, y su ⓘ. */
export function LeyendaNiveles() {
  const { estado } = useDemo();
  const u = estado?.umbrales_nivel;
  const texto = (nivel: (typeof NIVELES)[number]) => {
    if (!u) return NIVEL_LABEL[nivel];
    if (nivel === "baja") return `${NIVEL_LABEL[nivel]} < ${num(u.baja_menor_que)}%`;
    if (nivel === "alta") return `${NIVEL_LABEL[nivel]} > ${num(u.alta_mayor_que)}%`;
    return `${NIVEL_LABEL[nivel]} ${num(u.baja_menor_que)}–${num(u.alta_mayor_que)}%`;
  };
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-semibold text-co-navy">
      {NIVELES.map((nivel) => (
        <span key={nivel} className="flex items-center gap-1.5">
          <span className={`h-2.5 w-2.5 rounded-full ${NIVEL_BG[nivel]}`} />
          {texto(nivel)}
        </span>
      ))}
      <InfoTip termino="nivel" />
    </div>
  );
}

/**
 * Barras de ocupación por servicio. El ancho y el nivel (color) vienen del backend; las barras
 * crecen desde 0 con un pequeño escalonado.
 */
export default function GraficoOcupacion({ resumen }: { resumen: Resumen }) {
  return (
    <ul className="space-y-2.5">
      {resumen.servicios.map((s, i) => (
        <li
          key={s.service_id}
          className="grid grid-cols-[minmax(9rem,15rem)_1fr_4.5rem] items-center gap-4 text-sm"
          title={`${s.cupos_reservados} de ${s.cupos_liberados} cupos liberados reservados`}
        >
          <span className="text-right leading-tight">
            <span className="block font-bold text-co-navy">{s.nombre}</span>
            <span className="block text-xs font-semibold text-co-teal">{s.tipo_label}</span>
          </span>
          <Barra
            pct={s.ocupacion_pct}
            color={NIVEL_BG[s.nivel]}
            alto="h-3.5"
            retraso={i * 45}
            etiqueta={`${s.nombre}, ${s.tipo_label}: ${pct(s.ocupacion_pct)} de ocupación`}
          />
          <span className={`text-right text-base font-extrabold ${NIVEL_INK[s.nivel]}`}>
            <NumeroAnimado valor={s.ocupacion_pct} decimales={1} sufijo="%" duracion={700} />
          </span>
        </li>
      ))}
    </ul>
  );
}
