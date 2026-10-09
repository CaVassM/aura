// Vida académica simulada del estudiante (GET /api/estudiantes/{id}/academico/…). El calendario sale de D7.

export interface PersonaAcademica {
  id: string;
  nombre: string;
  carrera: string;
  institucion: string;
  distrito: string;
}

export interface SemanaEvaluacion {
  titulo: string;
  inicio: string;
  fin: string;
  intensidad: number;
  dias_para_inicio: number;
}

export interface PeriodoAcademico {
  id: string;
  nombre: string;
  inicio: string;
  fin: string;
  hoy: string;
  semana_actual: number;
  total_semanas: number;
  avance_pct: number;
  dias_para_cierre: number;
  evaluacion_actual: SemanaEvaluacion | null;
  proxima_evaluacion: SemanaEvaluacion | null;
}

export interface BloqueHorario {
  dia: number; // 0 = lunes
  dia_label: string;
  inicio: string;
  fin: string;
}

export interface AsistenciaCurso {
  sesiones: number;
  asistidas: number;
  faltas: number;
  tasa: number;
  bajo_minimo: boolean;
}

export interface AsistenciaGeneral {
  tasa: number;
  tasa_anterior: number;
  variacion: number;
  sesiones: number;
  asistidas: number;
  minimo: number;
}

export interface ProximaEvaluacion {
  nombre: string;
  fecha: string;
  dias: number;
  peso: number;
}

export interface CursoAcademico {
  id: string;
  codigo: string;
  nombre: string;
  docente: string;
  aula: string;
  creditos: number;
  horario: BloqueHorario[];
  asistencia: AsistenciaCurso;
  promedio_parcial: number | null;
  proxima_evaluacion: ProximaEvaluacion | null;
}

export interface RespuestaCursos {
  estudiante: PersonaAcademica;
  periodo: PeriodoAcademico;
  creditos: number;
  asistencia: AsistenciaGeneral;
  cursos: CursoAcademico[];
}

export type EstadoEvaluacion = "calificada" | "sin_publicar" | "programada";

export interface EvaluacionCurso {
  nombre: string;
  tipo: "control" | "parcial" | "trabajo" | "final";
  peso: number;
  fecha: string;
  nota: number | null;
  estado: EstadoEvaluacion;
}

export type SituacionCurso = "sin_notas" | "asegurado" | "alcanzable" | "fuera_de_alcance" | "aprobado" | "reprobado";

export interface NotasCurso {
  id: string;
  codigo: string;
  nombre: string;
  creditos: number;
  promedio_parcial: number | null;
  peso_evaluado: number;
  puntos: number;
  nota_necesaria: number | null;
  situacion: SituacionCurso;
  evaluaciones: EvaluacionCurso[];
}

export interface RespuestaCalificaciones {
  estudiante: PersonaAcademica;
  periodo: PeriodoAcademico;
  escala: { minima: number; maxima: number; aprobatoria: number };
  promedio_general: number | null;
  promedio_anterior: number;
  variacion: number | null;
  cursos: NotasCurso[];
}

export type TipoEventoCalendario =
  | "periodo_inicio"
  | "periodo_fin"
  | "semana_evaluacion"
  | "bienestar"
  | "actividad_universitaria"
  | "clase"
  | "evaluacion";

export interface EventoCalendario {
  id: string;
  tipo: TipoEventoCalendario;
  titulo: string;
  inicio: string;
  fin: string;
  intensidad?: number | null;
  institucion?: string | null;
  distrito?: string | null;
  hora_inicio?: string | null;
  hora_fin?: string | null;
  curso_id?: string | null;
  lugar?: string | null;
  peso?: number | null;
  estado?: string | null;
}

export interface RespuestaCalendario {
  estudiante: PersonaAcademica;
  periodo: PeriodoAcademico;
  cursos: { id: string; codigo: string; nombre: string }[];
  eventos: EventoCalendario[];
}
