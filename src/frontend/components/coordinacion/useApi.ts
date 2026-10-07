"use client";

import { useCallback, useEffect, useState } from "react";
import { useDemo } from "./DemoProvider";

interface Estado<T> {
  data: T | null;
  error: unknown;
  cargando: boolean;
}

/**
 * Pide datos al backend y los recarga cuando cambian `deps` o se reinicia la demo.
 * Mantiene los datos anteriores mientras llegan los nuevos (sin parpadeo al filtrar).
 */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const { version } = useDemo();
  const [estado, setEstado] = useState<Estado<T>>({
    data: null,
    error: null,
    cargando: true,
  });
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;
    setEstado((s) => ({ ...s, cargando: true, error: null }));
    fetcher()
      .then((data) => vivo && setEstado({ data, error: null, cargando: false }))
      .catch(
        (error) =>
          vivo && setEstado({ data: null, error, cargando: false }),
      );
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version, intento, ...deps]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);
  return { ...estado, reintentar };
}
