"""Vida académica del estudiante (simulada) y calendario D7."""

from pydantic import BaseModel, Field


class PersonaOut(BaseModel):
    id: str
    nombre: str
    carrera: str
    institucion: str
    distrito: str


class SemanaEvaluacionOut(BaseModel):
    titulo: str
    inicio: str
    fin: str
    intensidad: int
    dias_para_inicio: int


class PeriodoOut(BaseModel):
    id: str
    nombre: str
    inicio: str
    fin: str
    hoy: str
    semana_actual: int
    total_semanas: int
    avance_pct: int
    dias_para_cierre: int
    evaluacion_actual: SemanaEvaluacionOut | None
    proxima_evaluacion: SemanaEvaluacionOut | None


class BloqueOut(BaseModel):
    dia: int = Field(description="0 = lunes … 6 = domingo")
    dia_label: str
    inicio: str
    fin: str


class AsistenciaCursoOut(BaseModel):
    sesiones: int
    asistidas: int
    faltas: int
    tasa: float
    bajo_minimo: bool


class AsistenciaGeneralOut(BaseModel):
    tasa: float
    tasa_anterior: float
    variacion: float
    sesiones: int
    asistidas: int
    minimo: float


class ProximaEvaluacionOut(BaseModel):
    nombre: str
    fecha: str
    dias: int
    peso: int


class CursoOut(BaseModel):
    id: str
    codigo: str
    nombre: str
    docente: str
    aula: str
    creditos: int
    horario: list[BloqueOut]
    asistencia: AsistenciaCursoOut
    promedio_parcial: float | None
    proxima_evaluacion: ProximaEvaluacionOut | None


class CursosOut(BaseModel):
    estudiante: PersonaOut
    periodo: PeriodoOut
    creditos: int
    asistencia: AsistenciaGeneralOut
    cursos: list[CursoOut]


class EscalaOut(BaseModel):
    minima: float
    maxima: float
    aprobatoria: float


class EvaluacionOut(BaseModel):
    nombre: str
    tipo: str
    peso: int
    fecha: str
    nota: float | None
    estado: str = Field(description="calificada | sin_publicar | programada")


class NotasCursoOut(BaseModel):
    id: str
    codigo: str
    nombre: str
    creditos: int
    promedio_parcial: float | None
    peso_evaluado: int
    puntos: float
    nota_necesaria: float | None = Field(description="Nota promedio que falta en lo pendiente para llegar a 4,0")
    situacion: str = Field(description="sin_notas | asegurado | alcanzable | fuera_de_alcance | aprobado | reprobado")
    evaluaciones: list[EvaluacionOut]


class CalificacionesOut(BaseModel):
    estudiante: PersonaOut
    periodo: PeriodoOut
    escala: EscalaOut
    promedio_general: float | None
    promedio_anterior: float
    variacion: float | None
    cursos: list[NotasCursoOut]


class EventoCalendarioOut(BaseModel):
    id: str
    tipo: str = Field(
        description="periodo_inicio | periodo_fin | semana_evaluacion | bienestar | actividad_universitaria | clase | evaluacion"
    )
    titulo: str
    inicio: str
    fin: str
    intensidad: int | None = None
    institucion: str | None = None
    distrito: str | None = None
    hora_inicio: str | None = None
    hora_fin: str | None = None
    curso_id: str | None = None
    lugar: str | None = None
    peso: int | None = None
    estado: str | None = Field(default=None, description="clase: asistio | falto | programada. evaluacion: calificada | sin_publicar | programada")


class CursoResumenOut(BaseModel):
    id: str
    codigo: str
    nombre: str


class CalendarioOut(BaseModel):
    estudiante: PersonaOut
    periodo: PeriodoOut
    cursos: list[CursoResumenOut]
    eventos: list[EventoCalendarioOut]
