"use client";

import { numFijo } from "@/lib/format";
import { useCountUp } from "./useMovimiento";

/** Cifra con conteo ascendente y números tabulares (no se mueven al cambiar de dígito). */
export default function NumeroAnimado({
  valor,
  decimales = 0,
  sufijo = "",
  duracion = 900,
  className = "",
}: {
  valor: number;
  decimales?: number;
  sufijo?: string;
  duracion?: number;
  className?: string;
}) {
  const v = useCountUp(valor, duracion);
  return (
    <span className={`tabular ${className}`} aria-label={`${numFijo(valor, decimales)}${sufijo}`}>
      <span aria-hidden="true">
        {numFijo(v, decimales)}
        {sufijo}
      </span>
    </span>
  );
}
