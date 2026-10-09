// Tipos de la API de Coordinación (ver src/backend/docs/api_coordinacion.md).
// Los campos van en snake_case, igual que el JSON del backend.

export type Nivel = "baja" | "media" | "alta";
export type TipoServicio = "counseling" | "peer_support" | "career_guidance";

export interface EstadoDemo {
  hoy: string;
  semana_inicio: string;
  semana_fin: string;
  agenda_inicio: string;
  agenda_fin: string;
  agenda_abierta_inicio: string;
  agenda_abierta_fin: string;
  escenario: string;
  etiqueta: string;
  semilla: number;
  factor_demanda: number;
  proporcion_vespertino_trabaja: number;
  pedidos_desde: string;
  pedidos_hasta: string;
  agenda_abierta_semanas: number;
  ocupacion_inicial_pct: number; // % de cupos que el servicio ya tenía ocupados
  fraccion_liberada_pct: number; // % de los cupos libres que presta a AURA
  espera_linea_base_dias: number; // espera media observada en D2
  umbrales_nivel: { baja_menor_que: number; alta_mayor_que: number };
}

export interface Rango {
  desde: string;
  hasta: string;
}

export interface Kpis {
  citas_agendadas: number;
  espera_media_dias: number;
  espera_linea_base_dias: number;
  capacidad_agenda_abierta: number;
  libres_agenda_abierta: number;
  cupos_liberados: number;
  cupos_reservados: number;
  ocupacion_pct: number;
  desencuentros: number;
  atendidos_alternativa: number;
}

export interface ServicioResumen {
  service_id: string;
  nombre: string;
  tipo: TipoServicio;
  tipo_label: string;
  ocupacion_pct: number;
  nivel: Nivel;
  capacidad_semanal: number;
  capacidad_agenda_abierta: number;
  libres_agenda_abierta: number;
  cupos_liberados: number;
  cupos_reservados: number;
}

export interface Destino {
  tipo: string;
  tipo_label: string;
  cantidad: number;
}

/** Demanda de un tipo de servicio: cuánto se atendió en su tipo y cuánto se desvió por afinidad. */
export interface DemandaTipo {
  ideal: string;
  ideal_label: string;
  pedidos: number;
  atendidos_en_su_tipo: number;
  atendidos_con_alternativa: number;
  sin_cupo: number;
  destinos: Destino[];
}

export interface Resumen {
  agenda_abierta: Rango;
  pedidos: Rango;
  kpis: Kpis;
  demanda_por_tipo: DemandaTipo[];
  servicios: ServicioResumen[];
}

export interface HorarioTramo {
  dias: string[];
  desde: string;
  hasta: string;
}

export interface ServicioProps {
  service_id: string;
  nombre: string;
  tipo: TipoServicio;
  tipo_label: string;
  distrito: string;
  direccion: string | null;
  horario_texto: string;
  horario: HorarioTramo[];
  canales: string[];
  canales_label: string[];
  capacidad_semanal: number; // D6
  capacidad_agenda_abierta: number;
  libres_agenda_abierta: number;
  cupos_liberados: number;
  cupos_reservados: number;
  ocupacion_pct: number;
  nivel: Nivel;
  alta_demanda: boolean;
  eligibility: string | null;
  referral_information: string | null;
  pos: { x: number; y: number }; // 0–1; y crece hacia el sur (0 = norte)
}

export interface ServicioFeature {
  type: "Feature";
  id: string;
  geometry: { type: string; coordinates: number[] };
  properties: ServicioProps;
}

export interface ServiciosGeoJSON {
  type: "FeatureCollection";
  features: ServicioFeature[];
}

export interface FiltrosServicios {
  tipo?: string;
  canal?: string;
  solo_alta_demanda?: boolean;
  distrito?: string;
  nivel?: string;
}

export interface Franja {
  dia: string;
  desde: string;
  hasta: string;
}

export interface Desencuentro {
  id: string;
  fecha: string;
  motivo: string;
  motivo_label: string;
  servicio_ideal: string;
  servicio_ideal_label: string;
  distrito: string;
  franja: Franja;
  canales_aceptables: string[];
  canales_label: string[];
  grupo: string;
  grupo_label: string;
}

export interface MatrizDistritoServicio {
  distritos: string[];
  servicios: { tipo: string; label: string }[];
  celdas: number[][]; // [distrito][servicio]
  total_filas: number[];
  total_columnas: number[];
  total: number;
}

export interface FranjaPrincipal {
  texto: string; // "entre 19:00 y 21:00, lunes a viernes"
  porcentaje: number;
  desde: string;
  hasta: string;
  dias: string;
}

export interface Insight {
  texto: string;
  porcentaje: number;
  grupo: string | null;
  servicio_ideal: string | null;
  franja: Franja | null;
}

export interface DesencuentrosRespuesta {
  total: number;
  filtrados: number;
  pagina: number;
  paginas: number;
  items: Desencuentro[];
  matriz_distrito_servicio: MatrizDistritoServicio;
  franja_principal: FranjaPrincipal | null;
  insight: Insight; // sobre todos los desencuentros, sin filtros
  insight_filtro: Insight | null; // sobre el conjunto filtrado (null sin filtros)
}

export interface FiltrosDesencuentros {
  motivo?: string;
  distrito?: string;
  servicio_ideal?: string;
  grupo?: string;
}

export interface CuposDia {
  fecha: string;
  dia: string;
  capacidad: number;
  libres: number;
  liberados: number;
  reservados: number;
  abierto: boolean;
}

export interface ServicioDetalle {
  servicio: ServicioProps;
  demanda_del_tipo: DemandaTipo;
  recibidos_como_alternativa: { cantidad: number; origenes: Destino[] };
  cupos_por_dia: CuposDia[];
  desencuentros_recientes: Desencuentro[];
}

export interface Reglas {
  motivo_servicio: {
    provisional: boolean;
    items: {
      motivo: string;
      motivo_label: string;
      servicio: string;
      servicio_label: string;
    }[];
  };
  afinidad: {
    provisional: boolean;
    minimo_alternativa: number;
    minimo_provisional: boolean;
    tipos: { codigo: string; label: string }[];
    matriz: {
      ideal: string;
      ideal_label: string;
      valores: { tipo: string; tipo_label: string; valor: number }[];
    }[];
  };
  aviso: {
    provisional: boolean;
    puntaje_minimo: number;
    solo_semanas_evaluacion: boolean;
    evento_evaluacion: string | null;
    senales: {
      id: string;
      nombre: string;
      descripcion: string;
      umbral: number | string | string[];
      umbral_texto: string; // el umbral en español, para mostrar
    }[];
  };
  p_asistencia: {
    provisional: boolean;
    canales: { canal: string; canal_label: string; valor: number }[];
  };
  pesos: {
    provisional: boolean;
    terminos: { id: string; nombre: string; peso: number }[];
  };
}

// --- Actividad en vivo (GET /api/coordinacion/actividad y su flujo /stream) ---

export type TipoEvento =
  | "cita_reservada"
  | "cita_cancelada"
  | "desencuentro"
  | "servicio_en_lote"
  | "servicio_sale_de_lote"
  | "lote_abierto"
  | "lote_solicitud"
  | "lote_resuelto"
  | "lista_espera_alta"
  | "lista_espera_aviso";

export interface LoteEvento {
  id: number;
  estado: "abierto" | "resuelto";
  solicitudes: number;
  tamano_maximo: number;
  ventana_s: number;
  cierra_en: string | null;
  resultado: {
    asignados: number;
    sin_cupo: number;
    tiempo_s: number | null;
    espera_media: number | null;
    espera_media_llegada: number | null;
    mejora_sobre_llegada: boolean | null;
    error: string | null;
  } | null;
}

export interface EventoActividad {
  id: number;
  tipo: TipoEvento;
  /** Instante real del registro (ISO, UTC). */
  registrado_en: string;
  /** Fecha simulada de la demo en que ocurrió (`hoy`). */
  fecha_solicitud: string;
  origen: "chat" | "api" | "lote" | "sistema";
  estudiante_id: string | null;
  servicio: {
    service_id: string;
    nombre: string;
    tipo: string;
    tipo_label: string;
    distrito: string;
  } | null;
  /** Ocupación del servicio tras el evento (reservados / liberados de la agenda abierta). */
  ocupacion: {
    pct: number;
    antes_pct: number;
    reservados: number;
    liberados: number;
    nivel: Nivel;
    en_lote: boolean;
  } | null;
  lote: LoteEvento | null;
  /** Umbral de modo lote (solo en eventos de servicio_en_lote / servicio_sale_de_lote). */
  umbral_pct: number | null;
  cita: {
    cita_id: string;
    fecha: string;
    hora_inicio: string;
    hora_fin: string;
    canal: string;
    canal_label: string;
    dias_espera: number | null;
    es_alternativa: boolean;
  } | null;
  desencuentro: {
    registro_id: string;
    motivo: string;
    motivo_label: string;
    servicio_ideal: string;
    servicio_ideal_label: string;
    distrito: string;
    grupo: string;
    grupo_label: string;
    franjas: string;
    canales: string[];
  } | null;
  /** Lista de espera: alguien quedó esperando un cupo, o se le avisó de uno (`cupo`). */
  espera: {
    id: string;
    motivo_label: string;
    servicio_ideal: string;
    servicio_ideal_label: string;
    distrito: string;
    franjas: string;
    cupo: string | null;
  } | null;
}

export interface ActividadRespuesta {
  epoca: string;
  ultimo_id: number;
  eventos: EventoActividad[];
}


// --- Modo lote (GET /api/coordinacion/lotes) ---

export interface ServicioLote {
  service_id: string;
  nombre: string;
  tipo: string;
  tipo_label: string;
  distrito: string;
  pct: number;
  reservados: number;
  liberados: number;
  en_lote: boolean;
}

export interface SolicitudLote {
  posicion: number;
  estudiante_id: string;
  entrada_en: string;
  origen: string;
  motivo: string;
  motivo_label: string;
  distrito: string;
  grupo: string;
  grupo_label: string;
}

export interface MetricasLote {
  objetivo: number;
  asignados: number;
  desencuentros: number;
  espera_media: number;
  espera_diurnos: number;
  espera_nocturnos: number;
  z: Record<string, number>;
}

export interface AsignacionLote {
  estudiante_id: string;
  posicion_llegada: number;
  orden_asignacion: number;
  servicio_nombre: string;
  tipo_label: string;
  distrito: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  canal: string;
  canal_label: string;
  espera_dias: number;
  es_alternativa: boolean;
  cita_id: string;
}

export interface ResultadoLote {
  asignados: number;
  sin_cupo: number;
  tiempo_s: number | null;
  poblacion: number | null;
  generaciones: number | null;
  genetico: MetricasLote | null;
  llegada: MetricasLote | null;
  mejora_sobre_llegada: boolean | null;
  asignaciones: AsignacionLote[];
  sin_cupo_estudiantes: string[];
  error: string | null;
}

export interface LoteDetalle {
  id: number;
  estado: "abierto" | "resolviendo" | "resuelto";
  abierto_en: string;
  cierra_en: string;
  cerrado_en: string | null;
  solicitudes: SolicitudLote[];
  resultado: ResultadoLote | null;
}

export interface LotesRespuesta {
  umbral_pct: number;
  ventana_s: number;
  tamano_maximo: number;
  /** Hora del servidor: la cuenta regresiva se calcula con la diferencia con el reloj del navegador. */
  servidor_ahora: string;
  servicios: ServicioLote[];
  abierto: LoteDetalle | null;
  historial: LoteDetalle[];
}
