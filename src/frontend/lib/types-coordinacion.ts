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
  cupos_liberados: number;
  cupos_ocupados: number;
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
  cupos_liberados: number;
  cupos_ocupados: number;
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
  capacidad_semanal: number;
  cupos_liberados: number;
  cupos_ocupados: number;
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

export interface Heatmap {
  dias: string[];
  horas: number[];
  celdas: number[][];
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
  heatmap: Heatmap;
  insight: Insight;
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
  liberados: number;
  ocupados: number;
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
