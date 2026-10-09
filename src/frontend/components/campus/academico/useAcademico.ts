"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Carga una sección académica de la persona activa. Al cambiar de perfil (selector de la demo) vuelve a
 * pedirla y muestra el esqueleto mientras llega, para que el cambio se note con la animación de entrada.
 */
export function useAcademico<T>(cargar: (estudianteId: string) => Promise<T>, estudianteId: string) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);

  const pedir = useCallback(() => {
    let vigente = true;
    setDatos(null);
    setError(null);
    cargar(estudianteId)
      .then((d) => vigente && setDatos(d))
      .catch((e) => vigente && setError(e));
    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estudianteId]);

  useEffect(pedir, [pedir]);
  return { datos, error, reintentar: pedir };
}
