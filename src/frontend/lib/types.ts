// Tipos de la vista del estudiante. Reflejan el contrato real del backend (snake_case),
// documentado en src/backend/docs/api_agente.md. Los de Coordinación están en ./types-coordinacion.ts.

export type Role = "user" | "agent";

/** Tipos de servicio de la red (códigos de los datos). */
export type TipoServicio = "counseling" | "peer_support" | "career_guidance";

/**
 * Una opción de cita que propone el agente (todavía no está reservada). Es un cupo concreto (`tipo_opcion: "cupo"`) o un
 * servicio en modo lote (`"lote"`): sin día, hora ni canal, porque los decide el lote; al elegirla la solicitud queda
 * pendiente y el resultado llega después al mismo chat.
 */
export interface Opcion {
  opcion_id: string;
  tipo_opcion?: "cupo" | "lote";
  service_id: string;
  servicio_nombre: string;
  tipo: string;
  tipo_label: string;
  distrito: string;
  fecha: string; // AAAA-MM-DD (vacío en las de lote)
  hora_inicio: string; // HH:MM
  hora_fin: string;
  canal: string; // digital | phone | in_person
  dias_espera: number;
  es_alternativa: boolean;
  afinidad: number;
  /** Solo `lote`. */
  cupos_libres?: number | null;
  tiempo_respuesta_s?: number | null;
  /** Solo `lote`: texto listo para mostrar. */
  mensaje?: string | null;
}

export const esLote = (o: Pick<Opcion, "tipo_opcion">) => o.tipo_opcion === "lote";

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
  /** Línea de la confirmación según el canal (enlace por correo, llamada o lugar presencial). */
  aviso_canal?: string;
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

/** Aviso en vivo para la persona (flujo /api/estudiantes/{id}/avisos/stream). */
export interface AvisoEstudiante {
  id: number;
  estudiante_id: string;
  tipo: "lote_en_espera" | "lote_asignada" | "lote_sin_cupo" | "lote_error" | "cupo_disponible";
  registrado_en: string;
  lote_id?: number;
  mensaje?: string;
  cita?: Cita;
  /** `cupo_disponible`: el cupo que se liberó (opción lista para tocar). */
  opciones?: Opcion[];
  espera_id?: string;
}

/** Una persona en la lista de espera (GET /api/estudiantes/{id}/lista-espera). */
export interface Espera {
  id: string;
  estudiante_id: string;
  estado: "esperando" | "avisada" | "cancelada";
  creada_en: string;
  avisada_en: string | null;
  motivo_label: string;
  servicio_ideal: string;
  servicio_ideal_label: string;
  distrito: string;
  franjas: string;
  canales: string[];
  opcion: Opcion | null;
}

/** GET /api/estudiantes/{id}/aviso-proactivo: ¿se le muestra la tarjeta «un espacio para ti»? */
export interface AvisoProactivo {
  mostrar: boolean;
  elegible: boolean;
  descartado: boolean;
  puntaje: number;
  minimo: number;
  senales: { id: string; nombre: string; cumple: boolean }[];
  semana: { titulo: string; inicio: string; fin: string; intensidad: number; dias_para_inicio: number } | null;
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
  /** Texto del backend de la última búsqueda para los casos especiales (sin cupos, lote, servicio pedido sin cupo). */
  mensaje: string | null;
  /** R7: ya tiene una cita activa de ese tipo de servicio; si confirma, se cambia por la nueva. */
  ya_tiene_cita: { cita: Record<string, unknown>; mensaje: string } | null;
  lista_espera: { id: string; servicio_ideal_label: string; franjas: string } | null;
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
  /** La persona quedó en la lista de espera: se le avisará aquí si se libera un cupo. */
  listaEspera?: boolean;
  /** La persona quedó esperando en este lote. */
  lote?: LoteEstado;
  /** Mensaje que llegó por aviso en vivo (el lote se resolvió). */
  aviso?: AvisoEstudiante["tipo"];
  crisis?: boolean;
  error?: boolean;
  /** Opción que la persona eligió al tocar una tarjeta (para marcarla). */
  elegida?: string;
}
