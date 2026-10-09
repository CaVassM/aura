"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * Segundos que faltan para `cierraEn` (ISO UTC). Usa la hora del servidor (`servidorAhora`) para no depender
 * de que el reloj del navegador esté en hora. Devuelve `null` si no hay cierre.
 */
export function useCuentaRegresiva(cierraEn: string | null | undefined, servidorAhora: string | undefined) {
  // Diferencia entre el reloj del servidor y el del navegador, medida cuando llegan los datos.
  const desfase = useMemo(
    () => (servidorAhora ? Date.parse(servidorAhora) - Date.now() : 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [servidorAhora],
  );
  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    if (!cierraEn) return;
    const t = setInterval(() => setAhora(Date.now()), 250);
    return () => clearInterval(t);
  }, [cierraEn]);

  if (!cierraEn) return null;
  return Math.max(0, (Date.parse(cierraEn) - (ahora + desfase)) / 1000);
}

/** 83 → "1:23" */
export function mmss(segundos: number): string {
  const total = Math.ceil(segundos);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}
