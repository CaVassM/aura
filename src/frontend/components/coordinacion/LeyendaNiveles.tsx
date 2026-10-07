"use client";

import { useDemo } from "./DemoProvider";
import { NIVEL_BG, NIVEL_LABEL, NIVELES } from "./nivel";
import { num } from "@/lib/format";

/** Leyenda baja / media / alta con los umbrales que define el backend. */
export default function LeyendaNiveles({ className = "" }: { className?: string }) {
  const { estado } = useDemo();
  const u = estado?.umbrales_nivel;
  const texto = (nivel: (typeof NIVELES)[number]) => {
    if (!u) return NIVEL_LABEL[nivel];
    if (nivel === "baja") return `${NIVEL_LABEL[nivel]} < ${num(u.baja_menor_que)}%`;
    if (nivel === "alta") return `${NIVEL_LABEL[nivel]} > ${num(u.alta_mayor_que)}%`;
    return `${NIVEL_LABEL[nivel]} ${num(u.baja_menor_que)}–${num(u.alta_mayor_que)}%`;
  };
  return (
    <div
      className={`flex flex-wrap items-center gap-4 text-xs text-aura-gray ${className}`}
    >
      {NIVELES.map((nivel) => (
        <span key={nivel} className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${NIVEL_BG[nivel]}`} />
          {texto(nivel)}
        </span>
      ))}
    </div>
  );
}
