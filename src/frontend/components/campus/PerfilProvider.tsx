"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { PERFIL_INICIAL, PERFILES, PerfilEstudiante } from "@/lib/perfiles";

const CLAVE = "aura:perfil";

interface PerfilCtx {
  perfil: PerfilEstudiante;
  perfiles: PerfilEstudiante[];
  cambiar: (id: string) => void;
  /** Lo que muestra el marco del campus (nombre, rol, iniciales). */
  usuario: { name: string; role: string; initials: string; avatar: string };
}

const Ctx = createContext<PerfilCtx | null>(null);

/**
 * Perfil de estudiante activo en el campus (selector de la demo). Se recuerda por pestaña
 * (sessionStorage) para que no cambie al navegar entre Inicio, Bienestar y Mis citas.
 */
export function PerfilProvider({ children }: { children: ReactNode }) {
  const [perfil, setPerfil] = useState<PerfilEstudiante>(PERFIL_INICIAL);

  useEffect(() => {
    try {
      const guardado = PERFILES.find((p) => p.id === window.sessionStorage.getItem(CLAVE));
      if (guardado) setPerfil(guardado);
    } catch {
      /* sin almacenamiento: queda el perfil inicial */
    }
  }, []);

  const cambiar = useCallback((id: string) => {
    const nuevo = PERFILES.find((p) => p.id === id);
    if (!nuevo) return;
    setPerfil(nuevo);
    try {
      window.sessionStorage.setItem(CLAVE, id);
    } catch {
      /* ignorar */
    }
  }, []);

  const valor = useMemo<PerfilCtx>(
    () => ({
      perfil,
      perfiles: PERFILES,
      cambiar,
      usuario: { name: perfil.nombre, role: "Estudiante", initials: perfil.iniciales, avatar: perfil.avatar },
    }),
    [perfil, cambiar],
  );

  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}

export function usePerfil(): PerfilCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePerfil debe usarse dentro de <PerfilProvider> (app/campus/layout.tsx)");
  return ctx;
}
