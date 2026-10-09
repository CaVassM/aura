"""Vida académica simulada del estudiante: cursos, calificaciones, calendario y asistencia.

Los datos salen de `repositories/academico_repository.py` (simulados) y del calendario D7 (real).
La asistencia es lo único que se le entrega al agente conversacional (`asistencia_para_agente`);
las notas y el resto no salen de la plataforma hacia él.
"""

from datetime import date, timedelta
from math import ceil

from ..repositories.academico_repository import (
    ASISTENCIA_MINIMA,
    NOTA_APROBATORIA,
    NOTA_MAXIMA,
    NOTA_MINIMA,
    PERIODO_ACTUAL,
    PERIODO_ANTERIOR,
    Curso,
    EstudianteAcademico,
    EventoD7,
)
from ..repositories.app_state import AppState
from .errors import NotFoundError
from .etiquetas import Etiquetas

TIPOS_D7 = {
    "period_start": "periodo_inicio",
    "period_end": "periodo_fin",
    "evaluation_week": "semana_evaluacion",
    "wellbeing_activity": "bienestar",
    "university_activity": "actividad_universitaria",
}


def _redondeo(valor: float, decimales: int = 2) -> float:
    return round(valor + 1e-9, decimales)


def _nombre_periodo(periodo: str) -> str:
    _, anio, numero = periodo.split("_")
    return f"Período {numero} · {anio}"


class AcademicoService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)
        self._hoy: date = estado.hoy

    # --- datos base ---

    def _estudiante(self, estudiante_id: str) -> EstudianteAcademico:
        est = self._estado.academico.estudiante(estudiante_id)
        if est is None:
            raise NotFoundError(
                f"No hay datos académicos simulados para {estudiante_id}. "
                "Solo existen para los perfiles de la demo (STU_DEMO_001 … STU_DEMO_004)."
            )
        return est

    def _eventos_d7(self, est: EstudianteAcademico) -> list[EventoD7]:
        """Eventos D7 del período actual que le corresponden: `ALL` o su institución, y `ALL` o su distrito."""
        return [
            e
            for e in self._estado.academico.eventos_del_periodo(PERIODO_ACTUAL)
            if e.institucion in ("ALL", est.institucion) and e.distrito in ("ALL", est.distrito)
        ]

    def _semanas_evaluacion(self, eventos: list[EventoD7]) -> list[EventoD7]:
        return sorted((e for e in eventos if e.tipo == "evaluation_week"), key=lambda e: e.inicio)

    def _fechas_periodo(self, eventos: list[EventoD7]) -> tuple[date, date]:
        inicio = next(e.inicio for e in eventos if e.tipo == "period_start")
        fin = next(e.fin for e in eventos if e.tipo == "period_end")
        return inicio, fin

    def _sesiones(self, curso: Curso, eventos: list[EventoD7]) -> list[dict]:
        """Todas las sesiones del curso en el período, en orden. Sin clases en semanas de evaluación."""
        inicio, fin = self._fechas_periodo(eventos)
        evaluacion = self._semanas_evaluacion(eventos)
        sesiones = []
        dia = inicio
        while dia <= fin:
            if not any(e.inicio <= dia <= e.fin for e in evaluacion):
                for d, desde, hasta in curso.bloques:
                    if dia.weekday() == d:
                        sesiones.append({"fecha": dia, "inicio": desde, "fin": hasta})
            dia += timedelta(days=1)
        dictadas = 0
        for s in sesiones:
            s["dictada"] = s["fecha"] <= self._hoy
            if s["dictada"]:
                s["indice"] = dictadas
                dictadas += 1
                s["asistio"] = s["indice"] not in curso.faltas
        return sesiones

    # --- asistencia ---

    def _asistencia_curso(self, curso: Curso, eventos: list[EventoD7]) -> dict:
        dictadas = [s for s in self._sesiones(curso, eventos) if s["dictada"]]
        asistidas = sum(1 for s in dictadas if s["asistio"])
        tasa = asistidas / len(dictadas) if dictadas else 1.0
        return {
            "sesiones": len(dictadas),
            "asistidas": asistidas,
            "faltas": len(dictadas) - asistidas,
            "tasa": _redondeo(tasa, 3),
            "bajo_minimo": tasa < ASISTENCIA_MINIMA,
        }

    def _asistencia_general(self, est: EstudianteAcademico, eventos: list[EventoD7]) -> dict:
        por_curso = [self._asistencia_curso(c, eventos) for c in est.cursos]
        sesiones = sum(a["sesiones"] for a in por_curso)
        asistidas = sum(a["asistidas"] for a in por_curso)
        tasa = asistidas / sesiones if sesiones else 1.0
        previas, previas_asistidas = est.asistencia_anterior
        anterior = previas_asistidas / previas
        return {
            "tasa": _redondeo(tasa, 3),
            "tasa_anterior": _redondeo(anterior, 3),
            "variacion": _redondeo(tasa - anterior, 3),
            "sesiones": sesiones,
            "asistidas": asistidas,
            "minimo": ASISTENCIA_MINIMA,
        }

    def asistencia_para_agente(self, estudiante_id: str) -> dict:
        """Lo ÚNICO académico que ve el agente: la asistencia (tasa del período, el anterior y por curso).

        Sin notas, créditos ni alertas. No lanza si la persona no tiene datos simulados."""
        est = self._estado.academico.estudiante(estudiante_id)
        if est is None:
            return {
                "ok": False,
                "error": "sin_datos_academicos",
                "detalle": "No hay datos de asistencia para esta persona.",
            }
        eventos = self._eventos_d7(est)
        general = self._asistencia_general(est, eventos)
        return {
            "ok": True,
            "periodo": _nombre_periodo(PERIODO_ACTUAL),
            "periodo_anterior": _nombre_periodo(PERIODO_ANTERIOR),
            "asistencia_actual": general["tasa"],
            "asistencia_periodo_anterior": general["tasa_anterior"],
            "variacion": general["variacion"],
            "sesiones_dictadas": general["sesiones"],
            "sesiones_asistidas": general["asistidas"],
            "minimo_requerido": ASISTENCIA_MINIMA,
            "cursos": [
                {"curso": c.nombre, **{k: v for k, v in self._asistencia_curso(c, eventos).items()}}
                for c in est.cursos
            ],
        }

    # --- periodo ---

    def _periodo(self, eventos: list[EventoD7]) -> dict:
        inicio, fin = self._fechas_periodo(eventos)
        evaluacion = self._semanas_evaluacion(eventos)
        actual = next((e for e in evaluacion if e.inicio <= self._hoy <= e.fin), None)
        proxima = next((e for e in evaluacion if e.inicio > self._hoy), None)
        total_dias = (fin - inicio).days + 1
        transcurridos = min(max((self._hoy - inicio).days + 1, 0), total_dias)

        def semana(e: EventoD7 | None) -> dict | None:
            if e is None:
                return None
            return {
                "titulo": e.titulo,
                "inicio": e.inicio.isoformat(),
                "fin": e.fin.isoformat(),
                "intensidad": e.intensidad,
                "dias_para_inicio": (e.inicio - self._hoy).days,
            }

        return {
            "id": PERIODO_ACTUAL,
            "nombre": _nombre_periodo(PERIODO_ACTUAL),
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
            "hoy": self._hoy.isoformat(),
            "semana_actual": min(max((self._hoy - inicio).days // 7 + 1, 1), ceil(total_dias / 7)),
            "total_semanas": ceil(total_dias / 7),
            "avance_pct": round(100 * transcurridos / total_dias),
            "dias_para_cierre": max((fin - self._hoy).days, 0),
            "evaluacion_actual": semana(actual),
            "proxima_evaluacion": semana(proxima),
        }

    @staticmethod
    def _persona(est: EstudianteAcademico) -> dict:
        return {
            "id": est.id,
            "nombre": est.nombre,
            "carrera": est.carrera,
            "institucion": est.institucion,
            "distrito": est.distrito,
        }

    # --- notas ---

    def _estado_evaluacion(self, fecha: str, nota: float | None) -> str:
        if nota is not None:
            return "calificada"
        return "sin_publicar" if date.fromisoformat(fecha) <= self._hoy else "programada"

    def _notas_curso(self, curso: Curso) -> dict:
        calificadas = [e for e in curso.evaluaciones if e.nota is not None]
        peso_evaluado = sum(e.peso for e in calificadas)
        puntos = sum(e.nota * e.peso / 100 for e in calificadas)  # aportado a la nota final (escala 1–7)
        promedio = puntos / (peso_evaluado / 100) if peso_evaluado else None
        pendiente = 100 - peso_evaluado
        if peso_evaluado == 0:
            situacion, necesaria = "sin_notas", None
        else:
            necesaria = (NOTA_APROBATORIA - puntos) / (pendiente / 100) if pendiente else None
            if pendiente == 0:
                situacion = "aprobado" if puntos >= NOTA_APROBATORIA else "reprobado"
            elif necesaria <= NOTA_MINIMA:
                situacion = "asegurado"
            elif necesaria > NOTA_MAXIMA:
                situacion = "fuera_de_alcance"
            else:
                situacion = "alcanzable"
        return {
            "promedio_parcial": _redondeo(promedio, 1) if promedio is not None else None,
            "peso_evaluado": peso_evaluado,
            "puntos": _redondeo(puntos, 2),
            "nota_necesaria": _redondeo(necesaria, 1) if necesaria is not None and necesaria > NOTA_MINIMA else None,
            "situacion": situacion,
        }

    def _proxima_evaluacion(self, curso: Curso) -> dict | None:
        futuras = [e for e in curso.evaluaciones if e.nota is None and date.fromisoformat(e.fecha) > self._hoy]
        if not futuras:
            return None
        e = min(futuras, key=lambda x: x.fecha)
        return {"nombre": e.nombre, "fecha": e.fecha, "dias": (date.fromisoformat(e.fecha) - self._hoy).days, "peso": e.peso}

    def _horario(self, curso: Curso) -> list[dict]:
        return [
            {"dia": d, "dia_label": self._etiquetas.dia_largo(d), "inicio": desde, "fin": hasta}
            for d, desde, hasta in curso.bloques
        ]

    def _promedio_general(self, est: EstudianteAcademico) -> float | None:
        pares = [
            (self._notas_curso(c)["promedio_parcial"], c.creditos)
            for c in est.cursos
            if self._notas_curso(c)["promedio_parcial"] is not None
        ]
        creditos = sum(cr for _, cr in pares)
        return _redondeo(sum(p * cr for p, cr in pares) / creditos, 1) if creditos else None

    # --- vistas ---

    def cursos(self, estudiante_id: str) -> dict:
        est = self._estudiante(estudiante_id)
        eventos = self._eventos_d7(est)
        return {
            "estudiante": self._persona(est),
            "periodo": self._periodo(eventos),
            "creditos": sum(c.creditos for c in est.cursos),
            "asistencia": self._asistencia_general(est, eventos),
            "cursos": [
                {
                    "id": c.id,
                    "codigo": c.codigo,
                    "nombre": c.nombre,
                    "docente": c.docente,
                    "aula": c.aula,
                    "creditos": c.creditos,
                    "horario": self._horario(c),
                    "asistencia": self._asistencia_curso(c, eventos),
                    "promedio_parcial": self._notas_curso(c)["promedio_parcial"],
                    "proxima_evaluacion": self._proxima_evaluacion(c),
                }
                for c in est.cursos
            ],
        }

    def calificaciones(self, estudiante_id: str) -> dict:
        est = self._estudiante(estudiante_id)
        eventos = self._eventos_d7(est)
        general = self._promedio_general(est)
        return {
            "estudiante": self._persona(est),
            "periodo": self._periodo(eventos),
            "escala": {"minima": NOTA_MINIMA, "maxima": NOTA_MAXIMA, "aprobatoria": NOTA_APROBATORIA},
            "promedio_general": general,
            "promedio_anterior": est.promedio_anterior,
            "variacion": _redondeo(general - est.promedio_anterior, 1) if general is not None else None,
            "cursos": [
                {
                    "id": c.id,
                    "codigo": c.codigo,
                    "nombre": c.nombre,
                    "creditos": c.creditos,
                    **self._notas_curso(c),
                    "evaluaciones": [
                        {
                            "nombre": e.nombre,
                            "tipo": e.tipo,
                            "peso": e.peso,
                            "fecha": e.fecha,
                            "nota": e.nota,
                            "estado": self._estado_evaluacion(e.fecha, e.nota),
                        }
                        for e in c.evaluaciones
                    ],
                }
                for c in est.cursos
            ],
        }

    def calendario(self, estudiante_id: str) -> dict:
        est = self._estudiante(estudiante_id)
        d7 = self._eventos_d7(est)
        eventos: list[dict] = [
            {
                "id": e.id,
                "tipo": TIPOS_D7[e.tipo],
                "titulo": e.titulo,
                "inicio": e.inicio.isoformat(),
                "fin": e.fin.isoformat(),
                "intensidad": e.intensidad,
                "institucion": e.institucion,
                "distrito": e.distrito,
            }
            for e in d7
        ]
        for c in est.cursos:
            for n, s in enumerate(self._sesiones(c, d7)):
                eventos.append(
                    {
                        "id": f"{c.id}-S{n + 1}",
                        "tipo": "clase",
                        "titulo": c.nombre,
                        "inicio": s["fecha"].isoformat(),
                        "fin": s["fecha"].isoformat(),
                        "hora_inicio": s["inicio"],
                        "hora_fin": s["fin"],
                        "curso_id": c.id,
                        "lugar": c.aula,
                        "estado": ("asistio" if s["asistio"] else "falto") if s["dictada"] else "programada",
                    }
                )
            for e in c.evaluaciones:
                eventos.append(
                    {
                        "id": f"{c.id}-{e.tipo}",
                        "tipo": "evaluacion",
                        "titulo": f"{e.nombre} · {c.nombre}",
                        "inicio": e.fecha,
                        "fin": e.fecha,
                        "curso_id": c.id,
                        "peso": e.peso,
                        "estado": self._estado_evaluacion(e.fecha, e.nota),
                    }
                )
        eventos.sort(key=lambda x: (x["inicio"], x.get("hora_inicio", "")))
        return {
            "estudiante": self._persona(est),
            "periodo": self._periodo(d7),
            "cursos": [{"id": c.id, "codigo": c.codigo, "nombre": c.nombre} for c in est.cursos],
            "eventos": eventos,
        }
