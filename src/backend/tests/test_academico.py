"""Vida académica simulada (cursos, calificaciones, calendario D7) y la herramienta de asistencia del agente."""

import json
from datetime import date

import pytest

from app.repositories.academico_repository import ASISTENCIA_MINIMA, ESTUDIANTES

IDS = [e.id for e in ESTUDIANTES]


def test_los_cuatro_perfiles_tienen_datos(client):
    for id_ in IDS:
        r = client.get(f"/api/estudiantes/{id_}/academico/cursos")
        assert r.status_code == 200, r.text
        assert r.json()["cursos"] and r.json()["periodo"]["id"] == "PER_2026_4"


def test_estudiante_sin_datos_simulados_da_404(client):
    r = client.get("/api/estudiantes/STU_AE_000008/academico/cursos")
    assert r.status_code == 404 and r.json()["error"] == "no_encontrado"


def test_periodo_sale_de_d7(client):
    p = client.get("/api/estudiantes/STU_DEMO_001/academico/cursos").json()["periodo"]
    assert (p["inicio"], p["fin"]) == ("2026-10-05", "2026-12-23")
    assert p["hoy"] == "2026-11-15"
    # hoy es el último día de las evaluaciones intermedias; las finales son la próxima semana de evaluación
    assert p["evaluacion_actual"]["inicio"] == "2026-11-09" and p["evaluacion_actual"]["fin"] == "2026-11-15"
    assert p["proxima_evaluacion"]["inicio"] == "2026-12-10" and p["proxima_evaluacion"]["intensidad"] == 3
    assert p["semana_actual"] == 6 and p["total_semanas"] == 12


def test_la_asistencia_se_calcula_de_las_sesiones(client):
    a = client.get("/api/estudiantes/STU_DEMO_001/academico/cursos").json()
    # 5 semanas de clase antes de las evaluaciones: 4 cursos de 2 bloques + 1 de uno = 45 sesiones
    assert a["asistencia"]["sesiones"] == 45 and a["asistencia"]["asistidas"] == 36
    assert a["asistencia"]["tasa"] == 0.8 and a["asistencia"]["variacion"] == pytest.approx(-0.1)
    calculo = next(c for c in a["cursos"] if c["codigo"] == "MAT201")
    assert calculo["asistencia"] == {"sesiones": 10, "asistidas": 6, "faltas": 4, "tasa": 0.6, "bajo_minimo": True}


def test_todas_las_inasistencias_caen_en_sesiones_dictadas():
    for est in ESTUDIANTES:
        for curso in est.cursos:
            assert all(f >= 0 for f in curso.faltas)
            assert len(curso.faltas) == len(set(curso.faltas))


def test_calificaciones_ponderan_y_calculan_lo_que_falta(client):
    g = client.get("/api/estudiantes/STU_DEMO_001/academico/calificaciones").json()
    calculo = next(c for c in g["cursos"] if c["codigo"] == "MAT201")
    # control 15 % × 3,8 + parcial 30 % × 3,5 sobre el 45 % evaluado
    assert calculo["peso_evaluado"] == 45 and calculo["promedio_parcial"] == 3.6
    assert calculo["situacion"] == "alcanzable" and calculo["nota_necesaria"] == pytest.approx(4.3)
    estados = {e["tipo"]: e["estado"] for e in calculo["evaluaciones"]}
    assert estados == {"control": "calificada", "parcial": "calificada", "trabajo": "programada", "final": "programada"}
    bases = next(c for c in g["cursos"] if c["codigo"] == "BDA230")  # parcial rendido sin nota publicada
    assert next(e for e in bases["evaluaciones"] if e["tipo"] == "parcial")["estado"] == "sin_publicar"
    assert g["escala"] == {"minima": 1.0, "maxima": 7.0, "aprobatoria": 4.0}
    assert g["variacion"] == pytest.approx(g["promedio_general"] - g["promedio_anterior"], abs=0.05)


def test_notas_en_escala_y_pesos_suman_cien():
    for est in ESTUDIANTES:
        for curso in est.cursos:
            assert sum(e.peso for e in curso.evaluaciones) == 100
            assert all(e.nota is None or 1.0 <= e.nota <= 7.0 for e in curso.evaluaciones)


def test_calendario_respeta_institucion_y_distrito_de_d7(client):
    def eventos(id_):
        return client.get(f"/api/estudiantes/{id_}/academico/calendario").json()["eventos"]

    def tipos(id_, tipo):
        return [e["titulo"] for e in eventos(id_) if e["tipo"] == tipo]

    # Semana de pausa y bienestar: solo DIST_GAIA. Encuentro estudiantil: UNI_NOVA_AETHER en DIST_NEBULA.
    assert tipos("STU_DEMO_003", "bienestar") == ["Semana de pausa y bienestar 4"]  # Gaia
    assert tipos("STU_DEMO_001", "bienestar") == [] and tipos("STU_DEMO_002", "bienestar") == []
    assert tipos("STU_DEMO_001", "actividad_universitaria") == ["Encuentro estudiantil 4-1"]  # Nébula
    assert tipos("STU_DEMO_002", "actividad_universitaria") == []  # Vector: el de su distrito es de otra institución
    # Para toda la red: inicio, cierre y las dos semanas de evaluación
    for id_ in IDS:
        assert len(tipos(id_, "semana_evaluacion")) == 2
        assert tipos(id_, "periodo_inicio") and tipos(id_, "periodo_fin")


def test_calendario_sin_clases_en_semanas_de_evaluacion_y_con_asistencia(client):
    c = client.get("/api/estudiantes/STU_DEMO_001/academico/calendario").json()
    clases = [e for e in c["eventos"] if e["tipo"] == "clase"]
    assert clases
    for e in clases:
        dia = date.fromisoformat(e["inicio"])
        assert not (date(2026, 11, 9) <= dia <= date(2026, 11, 15)) and not (date(2026, 12, 10) <= dia <= date(2026, 12, 16))
        assert (e["estado"] == "programada") == (dia > date(2026, 11, 15))
    assert sum(1 for e in clases if e["estado"] == "falto") == 9
    # las evaluaciones de los cursos caen dentro de las semanas de evaluación de D7 (salvo control y trabajo)
    parciales = [e for e in c["eventos"] if e["tipo"] == "evaluacion" and e["titulo"].startswith("Examen parcial")]
    assert parciales and all("2026-11-09" <= e["inicio"] <= "2026-11-15" for e in parciales)
    finales = [e for e in c["eventos"] if e["tipo"] == "evaluacion" and e["titulo"].startswith("Examen final")]
    assert finales and all("2026-12-10" <= e["inicio"] <= "2026-12-16" for e in finales)


def test_asistencia_para_el_agente_no_trae_notas(estado_sembrado):
    from app.services.academico_service import AcademicoService

    r = AcademicoService(estado_sembrado).asistencia_para_agente("STU_DEMO_001")
    assert r["ok"] and r["asistencia_actual"] == 0.8 and r["asistencia_periodo_anterior"] == 0.9
    assert r["minimo_requerido"] == ASISTENCIA_MINIMA
    texto = json.dumps(r, ensure_ascii=False).lower()
    for prohibido in ("nota", "promedio", "credito", "alerta", "riesgo", "docente", "aula"):
        assert prohibido not in texto
    assert AcademicoService(estado_sembrado).asistencia_para_agente("STU_AE_1")["ok"] is False
