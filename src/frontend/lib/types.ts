// Tipos de la vista del estudiante. Reflejan el contrato real del backend (snake_case),
// documentado en src/backend/docs/api_agente.md. Los de Coordinación están en ./types-coordinacion.ts.

export type Role = "user" | "agent";

/** Tipos de servicio de la red (códigos de los datos). */
export type TipoServicio = "counseling" | "peer_support" | "career_guidance";

/** Una opción de cita que propone el agente (todavía no está reservada). */
export interface Opcion {
  opcion_id: string;
  service_id: string;
  servicio_nombre: string;
  tipo: string;
  tipo_label: string;
  distrito: string;
  fecha: string; // AAAA-MM-DD
  hora_inicio: string; // HH:MM
  hora_fin: string;
  canal: string; // digital | phone | in_person
  dias_espera: number;
  es_alternativa: boolean;
  afinidad: number;
}

export interface Cita {
  id: string;
  estudiante_id: string;
  service_id: string;
  servicio_nombre: string;
  tipo: string;
  tipo_label: string;
  distrito: string;
  hora_fin: string;
  slot: {
    id: string;
    service_id: string;
    fecha_iso: string; // AAAA-MM-DDTHH:MM:00 (inicio)
    disponible: boolean;
    canales: string[];
  };
  canal: string;
  estado: "confirmada" | "cancelada";
}

export interface HerramientaUsada {
  nombre: string;
  ok: boolean;
}

/** El lote en el que espera la persona (se cierra solo y asigna en conjunto). */
export interface LoteEstado {
  id: number;
  estado: "en_espera";
  posicion: number;
  solicitudes: number;
  tamano_maximo: number;
  /** ISO UTC: cuándo se cierra solo por tiempo. */
  cierra_en: string;
}

/** Lo que se ofrece cuando todo lo compatible está en servicios en modo lote. */
export interface LoteOferta {
  umbral_pct: number;
  ventana_s: number;
  tamano_maximo: number;
  abierto: boolean;
  pendientes: number;
  cierra_en: string | null;
  servicios: string[];
}

/** Aviso en vivo para la persona (flujo /api/estudiantes/{id}/avisos/stream). */
export interface AvisoEstudiante {
  id: number;
  estudiante_id: string;
  tipo: "lote_en_espera" | "lote_asignada" | "lote_sin_cupo" | "lote_error";
  registrado_en: string;
  lote_id?: number;
  mensaje?: string;
  cita?: Cita;
}

/** Respuesta de POST /api/chat. */
export interface ChatRespuesta {
  session_id: string;
  respuesta: string;
  opciones: Opcion[];
  cita: Cita | null;
  cita_cancelada: Cita | null;
  desencuentro_registrado: boolean;
  lote: LoteEstado | null;
  lote_oferta: LoteOferta | null;
  alerta_crisis: boolean;
  herramientas_usadas: HerramientaUsada[];
}

export interface HistorialChat {
  session_id: string;
  mensajes: { rol: Role; texto: string }[];
}

/** Un mensaje del chat tal como se pinta: texto más lo que el agente adjuntó. */
export interface ChatMessage {
  id: string;
  role: Role;
  text: string;
  opciones?: Opcion[];
  cita?: Cita;
  citaCancelada?: Cita;
  desencuentro?: boolean;
  /** La persona quedó esperando en este lote. */
  lote?: LoteEstado;
  /** Se ofrece entrar al lote (todo lo compatible está en modo lote). */
  loteOferta?: LoteOferta;
  /** Mensaje que llegó por aviso en vivo (el lote se resolvió). */
  aviso?: AvisoEstudiante["tipo"];
  crisis?: boolean;
  error?: boolean;
  /** Opción que la persona eligió al tocar una tarjeta (para marcarla). */
  elegida?: string;
}
