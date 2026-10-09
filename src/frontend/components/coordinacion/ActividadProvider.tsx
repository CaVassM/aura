"use client";

import { usePathname } from "next/navigation";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { getActividad, urlActividadStream } from "@/lib/api";
import { EventoActividad } from "@/lib/types-coordinacion";

export const RUTA_EN_VIVO = "/coordinacion/en-vivo";
const DURACION_AVISO_MS = 7000;
const MAXIMO_AVISOS = 4;

interface ActividadContexto {
  /** Lo nuevo, el más reciente primero. */
  eventos: EventoActividad[];
  conectado: boolean;
  /** Sube con cada evento (y al reiniciar la demo): las pantallas lo usan para recargar sus números. */
  version: number;
  /** Eventos llegados mientras no se miraba la pantalla En vivo. */
  sinVer: number;
  /** Hay un lote abierto (su última novedad no es una resolución). */
  loteAbierto: boolean;
  avisos: EventoActividad[];
  cerrarAviso: (id: number) => void;
}

const Contexto = createContext<ActividadContexto | null>(null);

/**
 * Registro en tiempo real de lo que hacen los estudiantes (citas reservadas o canceladas y desencuentros).
 * Carga lo ya registrado y luego escucha el flujo SSE del backend (`EventSource` reconecta solo).
 * Solo trae lo **nuevo**: las citas sembradas de la demo no aparecen.
 */
export function ActividadProvider({ children }: { children: ReactNode }) {
  const ruta = usePathname();
  const [eventos, setEventos] = useState<EventoActividad[]>([]);
  const [conectado, setConectado] = useState(false);
  const [version, setVersion] = useState(0);
  const [sinVer, setSinVer] = useState(0);
  const [avisos, setAvisos] = useState<EventoActividad[]>([]);
  const enVivo = useRef(false);
  enVivo.current = ruta === RUTA_EN_VIVO;

  const cerrarAviso = useCallback((id: number) => setAvisos((a) => a.filter((e) => e.id !== id)), []);

  useEffect(() => {
    if (ruta === RUTA_EN_VIVO) setSinVer(0);
  }, [ruta]);

  useEffect(() => {
    let cerrado = false;
    let fuente: EventSource | null = null;
    let ultimo = 0;
    const temporizadores = new Set<ReturnType<typeof setTimeout>>();

    const conectar = () => {
      if (cerrado) return;
      fuente = new EventSource(urlActividadStream(ultimo));
      fuente.addEventListener("inicio", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        setConectado(true);
        if (d.reinicio) {
          ultimo = 0;
          setEventos([]);
          setVersion((v) => v + 1);
        }
      });
      fuente.addEventListener("reinicio", () => {
        ultimo = 0;
        setEventos([]);
        setAvisos([]);
        setSinVer(0);
        setVersion((v) => v + 1);
      });
      fuente.addEventListener("actividad", (e) => {
        const evento: EventoActividad = JSON.parse((e as MessageEvent).data);
        if (evento.id <= ultimo) return;
        ultimo = evento.id;
        setEventos((prev) => (prev.some((x) => x.id === evento.id) ? prev : [evento, ...prev]));
        setVersion((v) => v + 1);
        if (!enVivo.current) setSinVer((n) => n + 1);
        setAvisos((a) => [evento, ...a].slice(0, MAXIMO_AVISOS));
        temporizadores.add(
          setTimeout(() => setAvisos((a) => a.filter((x) => x.id !== evento.id)), DURACION_AVISO_MS),
        );
      });
      fuente.onerror = () => setConectado(false); // EventSource vuelve a intentarlo solo
    };

    getActividad(0)
      .then((r) => {
        if (cerrado) return;
        ultimo = r.ultimo_id;
        setEventos([...r.eventos].reverse());
      })
      .catch(() => undefined)
      .finally(conectar);

    return () => {
      cerrado = true;
      fuente?.close();
      temporizadores.forEach(clearTimeout);
    };
  }, []);

  const loteAbierto = useMemo(() => {
    const ultimo = eventos.find((e) => e.tipo.startsWith("lote_"));
    return !!ultimo && ultimo.tipo !== "lote_resuelto";
  }, [eventos]);

  const valor = useMemo(
    () => ({ eventos, conectado, version, sinVer, loteAbierto, avisos, cerrarAviso }),
    [eventos, conectado, version, sinVer, loteAbierto, avisos, cerrarAviso],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useActividad(): ActividadContexto {
  const c = useContext(Contexto);
  if (!c) throw new Error("useActividad debe usarse dentro de ActividadProvider");
  return c;
}

/** Versión de la actividad sin exigir el proveedor (0 si no hay): para recargar datos al llegar eventos. */
export function useVersionActividad(): number {
  return useContext(Contexto)?.version ?? 0;
}
