"use client";

import { nombreTermino, Termino } from "@/lib/glosario";
import { numFijo } from "@/lib/format";
import Barra from "./Barra";
import { useDemo } from "./DemoProvider";
import InfoTip from "./InfoTip";
import NumeroAnimado from "./NumeroAnimado";

export interface DatosEmbudo {
  capacidad: number; // cupos del servicio en la agenda abierta
  libres: number; // tras la ocupación inicial
  liberados: number; // los que presta a AURA
  reservados: number; // los que AURA ya asignó
}

const PASOS: { clave: keyof DatosEmbudo; termino: Termino; corto: string; color: string }[] = [
  { clave: "capacidad", termino: "capacidad_agenda", corto: "Capacidad", color: "bg-co-teal/30" },
  { clave: "libres", termino: "libres", corto: "Libres", color: "bg-co-teal/50" },
  { clave: "liberados", termino: "liberados", corto: "Liberados", color: "bg-co-teal/75" },
  { clave: "reservados", termino: "reservados", corto: "Reservados", color: "bg-co-teal" },
];

const ancho = (valor: number, capacidad: number) =>
  capacidad > 0 ? (valor / capacidad) * 100 : 0;

/**
 * Embudo de cupos: Capacidad en 2 semanas → Libres → Liberados para AURA → Reservados por AURA.
 * - `completo`: etiquetas con ⓘ, cifra grande y barra por paso (drawer, resumen).
 * - `mini`: filas compactas para el tooltip del mapa.
 * - `fila`: 4 columnas con cifra y barrita, para una fila de tabla (el encabezado es `EncabezadoEmbudo`).
 */
export default function EmbudoCupos({
  datos,
  variante = "completo",
  columnas = 4,
}: {
  datos: DatosEmbudo;
  variante?: "completo" | "mini" | "fila";
  /** Columnas del embudo completo (2 en el drawer, 4 a todo el ancho). */
  columnas?: 2 | 4;
}) {
  const { glosario } = useDemo();

  if (variante === "mini") {
    return (
      <ul className="space-y-1" aria-label="Embudo de cupos">
        {PASOS.map((p, i) => (
          <li key={p.clave} className="grid grid-cols-[4.75rem_1fr_2.25rem] items-center gap-2 text-xs">
            <span className="font-semibold text-co-ink">{p.corto}</span>
            <Barra
              pct={ancho(datos[p.clave], datos.capacidad)}
              color={p.color}
              alto="h-1.5"
              retraso={i * 60}
            />
            <span className="tabular text-right font-bold text-co-navy">{numFijo(datos[p.clave], 0)}</span>
          </li>
        ))}
      </ul>
    );
  }

  if (variante === "fila") {
    return (
      <div className="grid grid-cols-4 gap-3">
        {PASOS.map((p, i) => (
          <div key={p.clave}>
            <div className="tabular text-sm font-bold text-co-navy">{numFijo(datos[p.clave], 0)}</div>
            <div className="mt-1">
              <Barra
                pct={ancho(datos[p.clave], datos.capacidad)}
                color={p.color}
                alto="h-1.5"
                retraso={i * 70}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-2 gap-x-5 gap-y-4 ${columnas === 4 ? "sm:grid-cols-4" : ""}`}>
      {PASOS.map((p, i) => (
        <div key={p.clave}>
          <div className="flex min-h-[1.25rem] items-start text-xs font-bold leading-tight text-co-navy">
            <span>{nombreTermino(p.termino, glosario)}</span>
            <InfoTip termino={p.termino} />
          </div>
          <div className="mt-1 text-2xl font-extrabold text-co-navy">
            <NumeroAnimado valor={datos[p.clave]} />
          </div>
          <div className="mt-1.5">
            <Barra
              pct={ancho(datos[p.clave], datos.capacidad)}
              color={p.color}
              alto="h-2"
              retraso={i * 90}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Encabezado de las 4 columnas del embudo para una tabla (con un ⓘ por paso). */
export function EncabezadoEmbudo() {
  const { glosario } = useDemo();
  return (
    <div className="grid grid-cols-4 gap-3 normal-case tracking-normal">
      {PASOS.map((p) => (
        <span key={p.clave} className="flex items-start text-xs font-bold leading-tight text-co-navy">
          <span>{nombreTermino(p.termino, glosario)}</span>
          <InfoTip termino={p.termino} />
        </span>
      ))}
    </div>
  );
}
