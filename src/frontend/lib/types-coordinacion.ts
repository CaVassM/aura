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
