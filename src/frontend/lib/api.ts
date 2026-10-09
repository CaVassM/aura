/**
 * Capa de datos de AURA: todas las pantallas hablan con el backend FastAPI (src/backend) a través de
 * este archivo; ningún componente hace fetch directo.
 *
 * - Estudiante (chat con el agente, "Mis citas"): contrato en src/backend/docs/api_agente.md.
 * - Coordinación: contrato en src/backend/docs/api_coordinacion.md.
 *
 * Todo el estado vive en la RAM del backend: si se reinicia, se pierden citas y conversaciones.
 */

import { ChatRespuesta, Cita, HistorialChat } from "./types";
import {
  ActividadRespuesta,
  DesencuentrosRespuesta,
  EstadoDemo,
  FiltrosDesencuentros,
  FiltrosServicios,
  Reglas,
  Resumen,
  ServicioDetalle,
  ServiciosGeoJSON,
} from "./types-coordinacion";

// ---------------------------------------------------------------------------
// Conexión con el backend
// ---------------------------------------------------------------------------

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"
).replace(/\/$/, "");

/**
 * Error de la API. `sinConexion` es true cuando el backend no respondió; `codigo` y `detalle` son los
 * del cuerpo `{"error", "detalle"}` del backend (p. ej. `agente_no_disponible`).
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly sinConexion: boolean,
    readonly status?: number,
    readonly codigo?: string,
    readonly detalle?: string,
  ) {
    super(message);
  }
}

type Params = Record<string, string | number | boolean | undefined | null>;

function consulta(params?: Params): string {
  const q = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "" && v !== false)
      q.set(k, String(v));
  });
  const texto = q.toString();
  return texto ? `?${texto}` : "";
}

async function request<T>(
  path: string,
  params?: Params,
  init?: RequestInit,
): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${API_BASE_URL}${path}${consulta(params)}`, init);
  } catch {
    throw new ApiError(
      `No se pudo conectar con el backend en ${API_BASE_URL}.`,
      true,
    );
  }
  if (!respuesta.ok) {
    let detalle = "";
    let codigo: string | undefined;
    try {
      const cuerpo = await respuesta.json();
      detalle = cuerpo.detalle || cuerpo.error || "";
      codigo = cuerpo.error;
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(
      `El backend respondió ${respuesta.status}${detalle ? `: ${detalle}` : ""}.`,
      false,
      respuesta.status,
      codigo,
      detalle,
    );
  }
  return respuesta.json() as Promise<T>;
}

export const getDemoEstado = () => request<EstadoDemo>("/api/demo/estado");

export const reiniciarDemo = () =>
  request<EstadoDemo>("/api/demo/reiniciar", undefined, { method: "POST" });

export const getResumen = (semana?: string) =>
  request<Resumen>("/api/coordinacion/resumen", { semana });

export const getServicios = (filtros: FiltrosServicios = {}) =>
  request<ServiciosGeoJSON>("/api/coordinacion/servicios", { ...filtros });

export const getServicioDetalle = (serviceId: string) =>
  request<ServicioDetalle>(
    `/api/coordinacion/servicios/${encodeURIComponent(serviceId)}`,
  );

export const getDesencuentros = (
  filtros: FiltrosDesencuentros = {},
  pagina = 1,
  tamano = 8,
) =>
  request<DesencuentrosRespuesta>("/api/coordinacion/desencuentros", {
    ...filtros,
    pagina,
    tamano,
  });

/** URL de descarga del CSV con los mismos filtros (el navegador lo descarga directo). */
export const urlDesencuentrosCsv = (filtros: FiltrosDesencuentros = {}) =>
  `${API_BASE_URL}/api/coordinacion/desencuentros.csv${consulta({ ...filtros })}`;

export const getReglas = () => request<Reglas>("/api/coordinacion/reglas");

/** Lo nuevo (citas y desencuentros hechos después de arrancar la demo), del más antiguo al más reciente. */
export const getActividad = (desde = 0) =>
  request<ActividadRespuesta>("/api/coordinacion/actividad", { desde });

/** URL del flujo en tiempo real (SSE); `desde` es el último id que ya se tiene. */
export const urlActividadStream = (desde = 0) =>
  `${API_BASE_URL}/api/coordinacion/actividad/stream?desde=${desde}`;

// ---------------------------------------------------------------------------
// Estudiante: chat con el agente y citas
// ---------------------------------------------------------------------------

export interface EnvioChat {
  mensaje: string;
  estudiante_id: string;
  /** Omitir en el primer mensaje; reenviar el que devolvió la respuesta anterior. */
  session_id?: string | null;
  /** Distrito del perfil (para citas presenciales); el agente permite cambiarlo conversando. */
  distrito?: string;
}

/** Un mensaje a AURA. Puede tardar de segundos a más de un minuto (modelo local). */
export const chatEnviar = (envio: EnvioChat) =>
  request<ChatRespuesta>("/api/chat", undefined, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...envio, session_id: envio.session_id ?? undefined }),
  });

/** La conversación guardada (404 si la sesión ya no existe, p. ej. tras reiniciar el backend). */
export const chatHistorial = (sessionId: string, estudianteId: string) =>
  request<HistorialChat>(`/api/chat/${encodeURIComponent(sessionId)}`, {
    estudiante_id: estudianteId,
  });

/** Borra la conversación (no cancela citas ya reservadas). */
export const chatReiniciar = (sessionId: string, estudianteId: string) =>
  request<{ ok: boolean }>(
    `/api/chat/${encodeURIComponent(sessionId)}`,
    { estudiante_id: estudianteId },
    { method: "DELETE" },
  );

/** Citas de la persona (la más reciente primero). */
export const getMisCitas = (estudianteId: string) =>
  request<Cita[]>("/api/appointments", { estudiante_id: estudianteId });

export const cancelarCita = (citaId: string, estudianteId: string) =>
  request<Cita>(
    `/api/appointments/${encodeURIComponent(citaId)}`,
    { estudiante_id: estudianteId },
    { method: "DELETE" },
  );
