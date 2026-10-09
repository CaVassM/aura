"use client";

import { ReactNode } from "react";
import { useListo } from "./useCuentaAnimada";

/** Anillo de progreso que se dibuja al aparecer. `valor` entre 0 y 1; `marca` (opcional) pinta una muesca, p. ej. el mínimo. */
export default function Anillo({
  valor,
  tamano = 112,
  grosor = 10,
  pista = "stroke-white/20",
  trazo = "stroke-white",
  marca,
  children,
}: {
  valor: number;
  tamano?: number;
  grosor?: number;
  pista?: string;
  trazo?: string;
  marca?: number;
  children?: ReactNode;
}) {
  const listo = useListo(120);
  const r = (tamano - grosor) / 2;
  const c = 2 * Math.PI * r;
  const centro = tamano / 2;
  const angulo = marca !== undefined ? marca * 360 - 90 : 0;
  return (
    <div className="relative shrink-0" style={{ width: tamano, height: tamano }}>
      <svg width={tamano} height={tamano} viewBox={`0 0 ${tamano} ${tamano}`} className="-rotate-90" aria-hidden="true">
        <circle cx={centro} cy={centro} r={r} fill="none" strokeWidth={grosor} className={pista} />
        <circle
          cx={centro}
          cy={centro}
          r={r}
          fill="none"
          strokeWidth={grosor}
          strokeLinecap="round"
          className={`${trazo} transition-[stroke-dashoffset] duration-[1200ms] ease-out`}
          strokeDasharray={c}
          strokeDashoffset={listo ? c * (1 - Math.min(Math.max(valor, 0), 1)) : c}
        />
      </svg>
      {marca !== undefined && (
        <svg width={tamano} height={tamano} viewBox={`0 0 ${tamano} ${tamano}`} className="absolute inset-0" aria-hidden="true">
          <line
            x1={centro + (r - grosor / 2 - 2) * Math.cos((angulo * Math.PI) / 180)}
            y1={centro + (r - grosor / 2 - 2) * Math.sin((angulo * Math.PI) / 180)}
            x2={centro + (r + grosor / 2 + 2) * Math.cos((angulo * Math.PI) / 180)}
            y2={centro + (r + grosor / 2 + 2) * Math.sin((angulo * Math.PI) / 180)}
            strokeWidth={2}
            className="stroke-co-amber"
          />
        </svg>
      )}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">{children}</div>
    </div>
  );
}
