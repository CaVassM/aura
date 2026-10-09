"""Pruebas de disponibilidad, estado en RAM y reglas en las herramientas del agente."""

import unittest
import json
from datetime import timedelta

from aura.herramientas.estado_agenda import AgendaViva
from aura.herramientas.herramientas import HerramientasAgente
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
        self.agenda = AgendaViva()
        self.herramientas = HerramientasAgente(self.agenda)
        self.solicitud = solicitud_diurna()
        self.propuestas = self.herramientas.proponer_opciones(self.solicitud, 3)
        self.assertTrue(self.propuestas["opciones"])

    def test_reserva_duplicada_falla(self):
        """Una misma opción solo puede ser tomada por la primera solicitud."""
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        self.assertTrue(self.agenda.reservar("A", opcion)["ok"])
        opciones_nuevas = self.herramientas.proponer_opciones(self.solicitud, 20)["opciones"]
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

    def test_estado_vive_solo_en_ram(self):
        """Una agenda nueva no hereda reservas ni desencuentros de otra instancia."""
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        self.assertTrue(self.agenda.reservar("A", opcion)["ok"])
        registro = self.herramientas.registrar_desencuentro(self.solicitud)
        self.assertEqual(registro["registro_id"], "DES-0000001")
        nueva = AgendaViva()
        self.assertEqual(nueva.reservas, {})
        self.assertEqual(nueva.desencuentros, [])

    def test_ejecutar_despacha_por_nombre_y_rechaza_desconocidas(self):
        """El despachador de tool calling devuelve JSON también ante errores."""
        resultado = self.herramientas.ejecutar("proponer_opciones", {"solicitud": self.solicitud, "k": 1})
        self.assertEqual(len(resultado["opciones"]), 1)
        self.assertEqual(self.herramientas.ejecutar("borrar_todo", {})["error"], "herramienta_desconocida")
        self.assertEqual(self.herramientas.ejecutar("reservar", {"x": 1})["error"], "argumentos_invalidos")

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
        opciones = self.herramientas.proponer_opciones(solicitud, 5)["opciones"]
        self.assertTrue(not opciones or all(o["es_alternativa"] for o in opciones))
        self.assertTrue(all(o["afinidad"] >= 0.5 for o in opciones))

    def test_la_ventana_de_una_solicitud_va_de_su_fecha_mas_1_a_mas_14_dias(self):
        """Con referencia anterior a hoy, los cupos fuera de [ref+1, ref+14] no son opciones."""
        modelo = self._modelo_solicitud()
        referencia = self.agenda.hoy - timedelta(days=5)
        opciones = self.agenda.opciones_validas(modelo, referencia)
        fechas = [self.agenda.cupo_por_id[o.cupo_id].fecha for o in opciones]
        self.assertTrue(fechas)
        self.assertGreater(min(fechas), referencia)
        self.assertLessEqual(max(fechas), referencia + timedelta(days=14))
        self.assertLess(max(fechas), max(c.fecha for c in self.agenda.cupos))  # había cupos más lejanos

    def test_reservar_fuera_de_la_ventana_falla(self):
        opcion = self.propuestas["opciones"][0]["opcion_id"]
        lejana = self.agenda.hoy - timedelta(days=30)
        self.assertEqual(
            self.agenda.reservar("A", opcion, lejana), {"ok": False, "error": "cupo_fuera_de_ventana"}
        )
        self.assertTrue(self.agenda.reservar("A", opcion)["ok"])

    def _modelo_solicitud(self):
        return self.herramientas.convertir_solicitud(self.solicitud)[0]


if __name__ == "__main__":
    unittest.main()


def test_proponer_no_repite_el_mismo_servicio_a_la_misma_hora(client_fresco, estado_fresco):
    """Varios cupos a la misma hora del mismo servicio son una sola opción para la persona."""
    solicitud = {
        "estudiante_id": "E_DUP",
        "motivo": "academic_pressure",
        "distrito": "DIST_NEBULA",
        "franjas": [{"dia": d, "desde": "09:00", "hasta": "21:00"} for d in ("Mon", "Tue", "Wed", "Thu", "Fri")],
        "canales_aceptables": ["digital", "phone", "in_person"],
    }
    opciones = client_fresco.post("/api/appointments/proposals?k=20", json=solicitud).json()["opciones"]
    claves = [(o["service_id"], o["fecha"], o["hora_inicio"], o["canal"]) for o in opciones]
    assert opciones and len(claves) == len(set(claves))
