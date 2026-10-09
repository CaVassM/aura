"""Vida académica SIMULADA de los estudiantes de la demo (ciudad ficticia de Aethera).

Ni D1 ni D7 traen cursos, horarios ni notas, así que aquí se inventan para los cuatro perfiles de la
demo (`STU_DEMO_###`, ver `src/frontend/lib/perfiles.ts`). Lo único real es el **calendario D7**, que fija
el período, las semanas de evaluación y las actividades por institución y distrito. Todo vive en RAM
y es determinista: no hay aleatoriedad, así que dos arranques muestran lo mismo.

Supuestos de la simulación (no salen de los datos):
- Cada curso se dicta en uno o dos bloques semanales y no hay clases en las semanas de evaluación
  (esas semanas se rinden evaluaciones, no se dictan clases).
- Escala de notas 1,0–7,0 (la de `average_grade` en D3); se aprueba con 4,0.
- Asistencia mínima para rendir el examen final: 70 %.
- Las inasistencias se indican por número de sesión (0 = primera sesión del curso en el período).
"""

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

PERIODO_ACTUAL = "PER_2026_4"
PERIODO_ANTERIOR = "PER_2026_3"
NOTA_MINIMA = 1.0
NOTA_MAXIMA = 7.0
NOTA_APROBATORIA = 4.0
ASISTENCIA_MINIMA = 0.70

# Bloque de clase: (día de la semana 0=lun, hora inicio, hora fin)
Bloque = tuple[int, str, str]


@dataclass(frozen=True)
class Evaluacion:
    nombre: str
    tipo: str  # control | parcial | trabajo | final
    peso: int  # % de la nota del curso
    fecha: str
    nota: float | None  # None: aún no rendida o sin publicar


@dataclass(frozen=True)
class Curso:
    id: str
    codigo: str
    nombre: str
    docente: str
    aula: str
    creditos: int
    bloques: tuple[Bloque, ...]
    faltas: tuple[int, ...]  # índices de sesión a las que NO asistió
    evaluaciones: tuple[Evaluacion, ...]


@dataclass(frozen=True)
class EstudianteAcademico:
    id: str
    nombre: str
    carrera: str
    institucion: str
    distrito: str
    cursos: tuple[Curso, ...]
    promedio_anterior: float  # promedio del período anterior (D3 `average_grade`)
    asistencia_anterior: tuple[int, int]  # (sesiones, asistidas) del período anterior (D3 `attendance_rate`)


@dataclass
class EventoD7:
    id: str
    periodo: str
    tipo: str
    titulo: str
    inicio: date
    fin: date
    institucion: str
    distrito: str
    intensidad: int


def _fecha(base: str, dias: int = 0) -> str:
    return (date.fromisoformat(base) + timedelta(days=dias)).isoformat()


def _evaluaciones(i: int, control: float | None, parcial: float | None, trabajo: float | None = None) -> tuple[Evaluacion, ...]:
    """Control, parcial (semana de evaluaciones intermedias de D7), trabajo y examen final (evaluaciones finales).

    `i` reparte las fechas entre los cursos de una misma persona para que no coincidan todas el mismo día."""
    return (
        Evaluacion("Control 1", "control", 15, _fecha("2026-10-19", i), control),
        Evaluacion("Examen parcial", "parcial", 30, _fecha("2026-11-09", i), parcial),
        Evaluacion("Trabajo aplicado", "trabajo", 20, _fecha("2026-12-03", i % 3), trabajo),
        Evaluacion("Examen final", "final", 35, _fecha("2026-12-10", i), None),
    )


def _curso(
    id_: str, codigo: str, nombre: str, docente: str, aula: str, creditos: int,
    bloques: tuple[Bloque, ...], faltas: tuple[int, ...], i: int,
    control: float | None, parcial: float | None,
) -> Curso:
    return Curso(id_, codigo, nombre, docente, aula, creditos, bloques, faltas, _evaluaciones(i, control, parcial))


ESTUDIANTES: tuple[EstudianteAcademico, ...] = (
    EstudianteAcademico(
        "STU_DEMO_001", "Lucía Mendoza", "Ingeniería de Datos", "UNI_NOVA_AETHER", "DIST_NEBULA",
        (
            _curso("C1", "MAT201", "Cálculo Multivariable", "Dra. Irene Valdés", "Torre Nova · 3-12", 5,
                   ((0, "08:00", "10:00"), (2, "08:00", "10:00")), (2, 3, 6, 7), 0, 3.8, 3.5),
            _curso("C2", "EST210", "Estadística Aplicada", "Mtro. Ciro Adler", "Torre Nova · 2-04", 4,
                   ((1, "10:00", "12:00"), (3, "10:00", "12:00")), (4, 8), 1, 4.6, 4.2),
            _curso("C3", "PRG220", "Estructuras de Datos", "Dr. Hugo Lavín", "Laboratorio Orión · 1", 5,
                   ((0, "14:00", "16:00"), (4, "14:00", "16:00")), (1,), 2, 5.4, 5.1),
            _curso("C4", "BDA230", "Bases de Datos", "Mtra. Selene Ruiz", "Laboratorio Orión · 2", 4,
                   ((2, "10:00", "12:00"), (4, "10:00", "12:00")), (5, 9), 3, 4.9, None),
            _curso("C5", "COM140", "Comunicación Académica", "Lic. Tomás Vera", "Edificio Aurora · 204", 3,
                   ((3, "16:00", "18:00"),), (), 4, 5.8, 6.0),
        ),
        5.2, (100, 90),
    ),
    EstudianteAcademico(
        "STU_DEMO_002", "Mateo Rivas", "Diseño Visual", "UNI_NOVA_AETHER", "DIST_VECTOR",
        (
            _curso("C1", "DIS210", "Tipografía y Composición", "Mtra. Alba Quiroz", "Taller Prisma · 1", 4,
                   ((1, "09:00", "11:00"), (3, "09:00", "11:00")), (3,), 0, 5.6, 5.9),
            _curso("C2", "DIS230", "Diseño de Interacción", "Dr. Félix Aranda", "Taller Prisma · 3", 5,
                   ((0, "14:00", "16:00"), (2, "14:00", "16:00")), (6,), 1, 5.0, 5.3),
            _curso("C3", "HIS150", "Historia del Diseño", "Lic. Marta Ibáñez", "Edificio Aurora · 110", 3,
                   ((4, "10:00", "12:00"),), (), 2, 6.1, None),
            _curso("C4", "PRO220", "Taller de Prototipado", "Mtro. Dante Olmos", "Laboratorio Orión · 4", 4,
                   ((0, "16:00", "18:00"), (3, "14:00", "16:00")), (8,), 3, 5.2, 5.0),
        ),
        4.9, (90, 79),
    ),
    EstudianteAcademico(
        "STU_DEMO_003", "Valentina Ortega", "Psicología", "UNI_NOVA_AETHER", "DIST_GAIA",
        (
            _curso("C1", "PSI210", "Psicología del Desarrollo", "Dra. Elena Márquez", "Edificio Aurora · 301", 4,
                   ((0, "10:00", "12:00"), (2, "10:00", "12:00")), (), 0, 6.2, 5.8),
            _curso("C2", "PSI230", "Métodos de Investigación", "Dr. Bruno Salcedo", "Edificio Aurora · 305", 5,
                   ((1, "08:00", "10:00"), (3, "08:00", "10:00")), (5,), 1, 5.5, 5.7),
            _curso("C3", "PSI250", "Neurociencia Cognitiva", "Dra. Noa Fierro", "Torre Gaia · 2-08", 5,
                   ((1, "14:00", "16:00"), (4, "08:00", "10:00")), (), 2, 5.9, None),
            _curso("C4", "ETI140", "Ética Profesional", "Lic. Rafael Cano", "Edificio Aurora · 112", 3,
                   ((2, "16:00", "18:00"),), (2,), 3, 6.4, 6.0),
        ),
        5.7, (90, 84),
    ),
    EstudianteAcademico(
        "STU_DEMO_004", "Diego Salas", "Administración de Empresas", "UNI_NOVA_AETHER", "DIST_HORIZON",
        (
            _curso("C1", "ADM210", "Contabilidad de Costos", "Mtro. Paulo Rentería", "Torre Nova · 1-06", 4,
                   ((0, "18:00", "20:00"), (2, "18:00", "20:00")), (1, 4, 8), 0, 4.4, 3.9),
            _curso("C2", "MKT220", "Marketing Estratégico", "Dra. Camila Sarmiento", "Torre Nova · 1-09", 4,
                   ((1, "18:00", "20:00"), (3, "18:00", "20:00")), (2, 6), 1, 5.2, 4.8),
            _curso("C3", "FIN230", "Finanzas Corporativas", "Dr. Ignacio Peralta", "Torre Nova · 2-01", 5,
                   ((0, "20:00", "22:00"), (4, "18:00", "20:00")), (3, 7), 2, 4.1, None),
            _curso("C4", "ECO150", "Microeconomía Aplicada", "Lic. Renata Lugo", "Edificio Aurora · 208", 4,
                   ((2, "20:00", "22:00"),), (0,), 3, 5.0, 4.6),
            _curso("C5", "LID140", "Liderazgo y Equipos", "Mtra. Inés Bravo", "Edificio Aurora · 210", 3,
                   ((3, "20:00", "22:00"),), (), 4, 6.0, 5.5),
        ),
        5.0, (100, 86),
    ),
)

POR_ID: dict[str, EstudianteAcademico] = {e.id: e for e in ESTUDIANTES}


def cargar_d7(ruta: Path) -> list[EventoD7]:
    """Lee el calendario académico D7 (compartido por todas las instituciones; algunas filas son de una sola)."""
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return [
            EventoD7(
                f_["calendar_event_id"], f_["period_id"], f_["event_type"], f_["title"],
                date.fromisoformat(f_["start_date"]), date.fromisoformat(f_["end_date"]),
                f_["institution_id"], f_["district_id"], int(f_["evaluation_intensity"] or 0),
            )
            for f_ in csv.DictReader(f)
        ]


@dataclass
class AcademicoRepository:
    """Calendario D7 + estudiantes simulados. Solo lectura: nada de aquí cambia durante la demo."""

    d7: list[EventoD7] = field(default_factory=list)

    @classmethod
    def desde_data_pack(cls, carpeta: Path) -> "AcademicoRepository":
        return cls(cargar_d7(carpeta / "D7_calendar.csv"))

    def estudiante(self, estudiante_id: str) -> EstudianteAcademico | None:
        return POR_ID.get(estudiante_id)

    def eventos_del_periodo(self, periodo: str) -> list[EventoD7]:
        return [e for e in self.d7 if e.periodo == periodo]
