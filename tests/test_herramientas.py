"""Pruebas de persistencia, disponibilidad y reglas en las herramientas del agente."""

import tempfile
import unittest
import json
from datetime import date, time
from pathlib import Path

from aura.herramientas.estado_agenda import AgendaViva
from aura.herramientas import herramientas as herramientas_api
from aura.herramientas.herramientas import proponer_opciones
from aura.herramientas.esquemas import esquemas_herramientas
from aura.motor.reglas import afinidad


def solicitud_diurna(estudiante="TEST_1"):
    """Construye una preferencia de consejería diurna para las pruebas."""
    return {
        "estudiante_id": estudiante,
        "motivo": "academic_pressure",
        "distrito": "DIST_GAIA",
        "grupo": "diurno",
        "franjas": [{"dia": "Tue", "desde": "09:00", "hasta": "18:00"}],
        "canales_aceptables": ["digital", "phone"],
    }


class HerramientasTests(unittest.TestCase):
    """Comprueba los efectos de reservar y cancelar sobre la agenda viva."""

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.agenda = AgendaViva(ruta_estado=Path(self.temporal.name) / "agenda.json")
        herramientas_api._AGENDA = self.agenda
        self.solicitud = solicitud_diurna()
        self.propuestas = proponer_opciones(self.solicitud, 3)
        self.assertTrue(self.propuestas["opciones"])

    def tearDown(self):
        herramientas_api._AGENDA = None
        self.temporal.cleanup()

    def test_reserva_duplicada_falla(self):
        """Una misma opción solo puede ser tomada por la primera solicitud."""
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        self.assertTrue(self.agenda.reservar("A", opcion)["ok"])
        opciones_nuevas = proponer_opciones(self.solicitud, 20)["opciones"]
        self.assertNotIn(opcion, {fila["opcion_id"] for fila in opciones_nuevas})
        resultado = self.agenda.reservar("B", opcion)
        self.assertEqual(resultado, {"ok": False, "error": "cupo_ya_tomado"})

    def test_esquemas_se_pueden_serializar_y_declaran_las_cuatro_llamadas(self):
        """Las declaraciones cumplen JSON y contienen las cuatro herramientas."""
        esquemas = esquemas_herramientas()
        json.dumps(esquemas, ensure_ascii=False)
        nombres = {esquema["name"] for esquema in esquemas}
        self.assertEqual(
            nombres,
            {
                "proponer_opciones",
                "reservar",
                "registrar_desencuentro",
                "cancelar_cita",
            },
        )

    def test_cancelar_libera_y_permite_reservar(self):
        """Una cancelación retira la ocupación persistente del cupo reservado."""
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        primera = self.agenda.reservar("A", opcion)
        self.assertTrue(self.agenda.cancelar(primera["cita"]["cita_id"])["ok"])
        segunda = self.agenda.reservar("B", opcion)
        self.assertTrue(segunda["ok"])

    def test_reserva_se_conserva_tras_reiniciar_agenda(self):
        """El estado JSON evita que una cita viva vuelva a ofrecerse al reiniciar."""
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        self.assertTrue(self.agenda.reservar("A", opcion)["ok"])
        recargada = AgendaViva(ruta_estado=self.agenda.ruta_estado)
        self.assertIn(opcion.split("|")[0], recargada.cupos_ocupados())
        self.assertEqual(
            recargada.reservar("B", opcion), {"ok": False, "error": "cupo_ya_tomado"}
        )

    def test_opciones_propuestas_respetan_reglas_y_disponibilidad(self):
        """Las propuestas deben ser libres, futuras, horarias y afines."""
        modelo = self._modelo_solicitud()
        validas = self.agenda.opciones_validas(modelo)
        esperadas = {f"{op.cupo_id}|{op.canal}" for op in validas}
        for salida in self.propuestas["opciones"]:
            identificador = salida["opcion_id"]
            self.assertIn(identificador, esperadas)
            cupo_id, canal = identificador.split("|")
            cupo = self.agenda.cupo_por_id[cupo_id]
            self.assertNotIn(cupo_id, self.agenda.cupos_ocupados())
            self.assertGreater(cupo.fecha, self.agenda.hoy)
            self.assertIn(canal, modelo.canales_aceptables)
            self.assertTrue(
                any(
                    f.dia_semana == cupo.fecha.weekday()
                    and f.hora_inicio <= cupo.hora_inicio
                    and cupo.hora_fin <= f.hora_fin
                    for f in modelo.franjas
                )
            )
            self.assertGreaterEqual(afinidad(modelo.servicio_ideal, cupo.tipo), 0.5)
            if canal == "in_person":
                self.assertEqual(cupo.distrito, modelo.distrito)

    def test_nocturno_que_trabaja_recibe_solo_alternativa_afín(self):
        """La solicitud nocturna no debe ofrecer consejería fuera de horario."""
        solicitud = {
            "estudiante_id": "NOCTURNO",
            "motivo": "academic_pressure",
            "distrito": "DIST_GAIA",
            "grupo": "nocturno",
            "franjas": [{"dia": "Tue", "desde": "19:00", "hasta": "21:00"}],
            "canales_aceptables": ["phone"],
        }
        opciones = proponer_opciones(solicitud, 5)["opciones"]
        self.assertTrue(not opciones or all(o["es_alternativa"] for o in opciones))
        self.assertTrue(all(o["afinidad"] >= 0.5 for o in opciones))

    def _modelo_solicitud(self):
        from aura.herramientas.herramientas import _convertir_solicitud

        return _convertir_solicitud(self.solicitud)[0]


if __name__ == "__main__":
    unittest.main()
