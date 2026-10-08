"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { getDemoEstado, reiniciarDemo } from "@/lib/api";
import { ContextoGlosario, contextoGlosario } from "@/lib/glosario";
import { EstadoDemo } from "@/lib/types-coordinacion";

interface DemoContexto {
  estado: EstadoDemo | null;
  /** Números del glosario (porcentajes, semanas, umbrales) tomados de /api/demo/estado. */
  glosario: ContextoGlosario;
  error: unknown;
  cargando: boolean;
  /** Sube cada vez que la demo se reinicia: las pantallas lo usan para recargar sus datos. */
  version: number;
  reintentar: () => void;
  reiniciar: () => Promise<void>;
}

const Contexto = createContext<DemoContexto | null>(null);

/** Estado de la demo (escenario, fechas, umbrales) compartido por las pantallas de Coordinación. */
export function DemoProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<EstadoDemo | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [cargando, setCargando] = useState(true);
  const [version, setVersion] = useState(0);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;
    setCargando(true);
    getDemoEstado()
      .then((e) => {
        if (!vivo) return;
        setEstado(e);
        setError(null);
      })
      .catch((e) => vivo && setError(e))
      .finally(() => vivo && setCargando(false));
    return () => {
      vivo = false;
    };
  }, [intento]);

  const glosario = useMemo(() => contextoGlosario(estado), [estado]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);

  const reiniciar = useCallback(async () => {
    const nuevo = await reiniciarDemo();
    setEstado(nuevo);
    setError(null);
    setVersion((v) => v + 1);
  }, []);

  return (
    <Contexto.Provider
      value={{ estado, glosario, error, cargando, version, reintentar, reiniciar }}
    >
      {children}
    </Contexto.Provider>
  );
}

export function useDemo(): DemoContexto {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useDemo debe usarse dentro de DemoProvider");
  return contexto;
}
