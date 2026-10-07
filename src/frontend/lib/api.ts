/**
 * Capa de datos de AURA.
 *
 * HOY: todo está simulado (mock) con datos fijos y un pequeño delay,
 * para que la interfaz funcione de punta a punta sin depender del backend.
 *
 * CUANDO CAMILO/LEO EXPONGAN LOS ENDPOINTS:
 * reemplaza el cuerpo de cada función por un fetch() a
 * `${process.env.NEXT_PUBLIC_API_URL}/...`. La forma de cada función
 * (nombre, parámetros, lo que devuelve) no debería cambiar — por eso
 * los componentes nunca llaman a fetch directamente, siempre llaman
 * a estas funciones. Ver README sección 6 para el ejemplo completo.
 */

import {
  Appointment,
  ChatResponse,
  ServiceOption,
  TimeSlot,
} from "./types";
import {
  DesencuentrosRespuesta,
  EstadoDemo,
  FiltrosDesencuentros,
  FiltrosServicios,
  Reglas,
  Resumen,
  ServicioDetalle,
  ServiciosGeoJSON,
} from "./types-coordinacion";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const MOCK_SERVICES: ServiceOption[] = [
  {
    id: "srv-1",
    nombre: "Consejería psicológica individual",
    modalidad: "presencial",
    esperaEstimadaDias: 4,
    descripcion: "Sesión 1:1 con un profesional de bienestar estudiantil.",
  },
  {
    id: "srv-2",
    nombre: "Orientación por chat con especialista",
    modalidad: "online",
    esperaEstimadaDias: 2,
    descripcion: "Conversación guiada para casos de sobrecarga puntual.",
  },
  {
    id: "srv-3",
    nombre: "Línea de ayuda telefónica",
    modalidad: "telefónico",
    esperaEstimadaDias: 1,
    descripcion: "Atención inmediata para hablar con alguien ahora mismo.",
  },
];

/** Simula la respuesta del agente conversacional de AURA. */
export async function sendMessage(text: string): Promise<ChatResponse> {
  await delay(600);

  const needsHelp =
    /estr[eé]s|ansiedad|sobrecarga|agobiad|abrumad|cansad|ayuda|parcial/i.test(
      text
    );

  if (!needsHelp) {
    return {
      reply:
        "Cuéntame un poco más — ¿cómo te has sentido con la carga académica últimamente?",
    };
  }

  return {
    reply:
      "Gracias por contarme. No diagnostico ni reemplazo atención profesional, pero puedo conectarte con un servicio disponible. Según lo que describes, estas opciones podrían ayudarte:",
    services: MOCK_SERVICES,
  };
}

/** Horarios disponibles para un servicio. */
export async function getAvailableSlots(
  serviceId: string
): Promise<TimeSlot[]> {
  await delay(400);
  const base = new Date();
  return Array.from({ length: 4 }).map((_, i) => {
    const d = new Date(base);
    d.setDate(base.getDate() + i + 1);
    d.setHours(9 + i * 2, 0, 0, 0);
    return {
      id: `slot-${serviceId}-${i}`,
      serviceId,
      fechaISO: d.toISOString(),
      disponible: true,
    };
  });
}

/** Confirma una cita y la guarda en localStorage (reemplazar por POST real). */
export async function bookAppointment(
  service: ServiceOption,
  slot: TimeSlot
): Promise<Appointment> {
  await delay(500);
  const appointment: Appointment = {
    id: `apt-${Date.now()}`,
    serviceId: service.id,
    serviceName: service.nombre,
    slot,
    estado: "confirmada",
  };

  if (typeof window !== "undefined") {
    const raw = window.localStorage.getItem("aura:appointments");
    const list: Appointment[] = raw ? JSON.parse(raw) : [];
    list.unshift(appointment);
    window.localStorage.setItem("aura:appointments", JSON.stringify(list));
  }

  return appointment;
}

/** Lee las citas guardadas (mock de "Mis citas"). */
export function getMyAppointments(): Appointment[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem("aura:appointments");
  return raw ? JSON.parse(raw) : [];
}

// ---------------------------------------------------------------------------
// Coordinación: datos reales del backend (FastAPI). Ningún componente hace fetch directo.
// ---------------------------------------------------------------------------

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"
).replace(/\/$/, "");

/** Error de la API. `sinConexion` es true cuando el backend no respondió. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly sinConexion: boolean,
    readonly status?: number,
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
    try {
      const cuerpo = await respuesta.json();
      detalle = cuerpo.detalle || cuerpo.error || "";
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(
      `El backend respondió ${respuesta.status}${detalle ? `: ${detalle}` : ""}.`,
      false,
      respuesta.status,
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
