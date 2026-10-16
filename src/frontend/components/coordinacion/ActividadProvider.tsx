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
/** Cada cuántos segundos se consulta el registro cuando no hay flujo en tiempo real. */
export const SONDEO_S = 3;
/** Si el flujo no confirma la conexión en este tiempo, se empieza a consultar el registro. */
const ESPERA_FLUJO_MS = 4000;

/** `en_vivo`: llega por el flujo SSE; `sondeo`: sin flujo, se consulta cada `SONDEO_S` s; `conectando`: aún sin saber. */
export type EstadoConexion = "conectando" | "en_vivo" | "sondeo";

interface ActividadContexto {
  /** Lo nuevo, el más reciente primero. */
  eventos: EventoActividad[];
  /** El flujo en tiempo real está activo (`estado === "en_vivo"`). */
  conectado: boolean;
  estado: EstadoConexion;
  /** Texto del indicador: «En vivo», «Actualizando cada 3 s» o «Conectando…». Nunca «Reconectando…» si el registro se actualiza. */
  etiquetaConexion: string;
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
 * Carga lo ya registrado y luego escucha el flujo SSE del backend (`EventSource` reconecta solo). Si el flujo no
 * llega (un túnel o proxy que lo corta o lo retiene), consulta el registro cada `SONDEO_S` segundos: el registro se
 * actualiza igual y el indicador lo dice con claridad.
 * Solo trae lo **nuevo**: las citas sembradas de la demo no aparecen.
 */
export function ActividadProvider({ children }: { children: ReactNode }) {
  const ruta = usePathname();
  const [eventos, setEventos] = useState<EventoActividad[]>([]);
  const [estado, setEstado] = useState<EstadoConexion>("conectando");
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
    let epoca: string | null = null;
    let sondeo: ReturnType<typeof setInterval> | null = null;
    let espera: ReturnType<typeof setTimeout> | null = null;
    const temporizadores = new Set<ReturnType<typeof setTimeout>>();

    const reiniciar = () => {
      ultimo = 0;
      setEventos([]);
      setAvisos([]);
      setSinVer(0);
      setVersion((v) => v + 1);
    };

    // Un evento nuevo, venga del flujo o del sondeo (el id evita repetirlo si llegan por los dos).
    const recibir = (evento: EventoActividad) => {
      if (evento.id <= ultimo) return;
      ultimo = evento.id;
      setEventos((prev) => (prev.some((x) => x.id === evento.id) ? prev : [evento, ...prev]));
      setVersion((v) => v + 1);
      if (!enVivo.current) setSinVer((n) => n + 1);
      setAvisos((a) => [evento, ...a].slice(0, MAXIMO_AVISOS));
      temporizadores.add(
        setTimeout(() => setAvisos((a) => a.filter((x) => x.id !== evento.id)), DURACION_AVISO_MS),
      );
    };

    const consultar = () =>
      getActividad(ultimo)
        .then((r) => {
          if (cerrado) return;
          if (epoca !== null && r.epoca !== epoca) {
            // La demo (o el backend) se reinició: se parte de cero con lo que haya.
            epoca = r.epoca;
            reiniciar();
            [...r.eventos].forEach(recibir);
            return;
          }
          epoca = r.epoca;
          r.eventos.forEach(recibir);
        })
        .catch(() => undefined);

    const detenerSondeo = () => {
      if (sondeo) clearInterval(sondeo);
      sondeo = null;
    };
    const iniciarSondeo = () => {
      if (cerrado || sondeo) return;
      setEstado("sondeo");
      consultar();
      sondeo = setInterval(consultar, SONDEO_S * 1000);
    };
    const flujoActivo = () => {
      if (espera) clearTimeout(espera);
      espera = null;
      detenerSondeo();
      setEstado("en_vivo");
    };

    const conectar = () => {
      if (cerrado) return;
      fuente = new EventSource(urlActividadStream(ultimo));
      espera = setTimeout(iniciarSondeo, ESPERA_FLUJO_MS);
      fuente.addEventListener("inicio", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        epoca = d.epoca ?? epoca;
        flujoActivo();
        if (d.reinicio) {
          ultimo = 0;
          setEventos([]);
          setVersion((v) => v + 1);
        }
      });
      fuente.addEventListener("reinicio", () => {
        reiniciar();
      });
      fuente.addEventListener("actividad", (e) => {
        flujoActivo();
        recibir(JSON.parse((e as MessageEvent).data));
      });
      // EventSource vuelve a intentarlo solo; mientras tanto el registro se sigue actualizando por sondeo.
      fuente.onerror = () => iniciarSondeo();
    };

    getActividad(0)
      .then((r) => {
        if (cerrado) return;
        ultimo = r.ultimo_id;
        epoca = r.epoca;
        setEventos([...r.eventos].reverse());
      })
      .catch(() => undefined)
      .finally(conectar);

    return () => {
      cerrado = true;
      fuente?.close();
      detenerSondeo();
      if (espera) clearTimeout(espera);
      temporizadores.forEach(clearTimeout);
    };
  }, []);

  const loteAbierto = useMemo(() => {
    const ultimo = eventos.find((e) => e.tipo.startsWith("lote_"));
    return !!ultimo && ultimo.tipo !== "lote_resuelto";
  }, [eventos]);

  const valor = useMemo<ActividadContexto>(
    () => ({
      eventos,
      conectado: estado === "en_vivo",
      estado,
      etiquetaConexion:
        estado === "en_vivo" ? "En vivo" : estado === "sondeo" ? `Actualizando cada ${SONDEO_S} s` : "Conectando…",
      version,
      sinVer,
      loteAbierto,
      avisos,
      cerrarAviso,
    }),
    [eventos, estado, version, sinVer, loteAbierto, avisos, cerrarAviso],
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
