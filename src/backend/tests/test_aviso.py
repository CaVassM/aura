"""Pruebas pequeñas para las reglas de puntuación del aviso académico."""

import unittest

from aura.aviso.filtros import calcular_senales


class FiltrosAvisoTests(unittest.TestCase):
    """Confirma que dos señales califican y una sola no alcanza el umbral."""

    def test_dos_senales_elegible_una_no(self):
        anterior = "PER_2026_1"
        actual = "PER_2026_2"
        d3 = [
            self._fila("A", anterior, 20, 0.80, 0, "low"),
            self._fila("B", anterior, 10, 0.80, 0, "low"),
            self._fila("C", anterior, 30, 0.80, 0, "low"),
            self._fila("D", anterior, 40, 0.80, 0, "low"),
            self._fila("A", actual, 20, 0.80, -0.6, "medium"),
            self._fila("B", actual, 10, 0.80, 0, "medium"),
            self._fila("C", actual, 30, 0.70, 0, "low"),
            self._fila("D", actual, 40, 0.75, 0, "low"),
        ]
        umbrales = {
            "dropout_alert": ["medium", "high"],
            "caida_asistencia": 0.05,
            "cambio_nota": -0.5,
            "percentil_carga_creditos": 0.75,
            "puntaje_minimo": 2,
        }
        filas = {
            f["estudiante_id"]: f
            for f in calcular_senales(actual, d3, anterior, umbrales)
        }
        self.assertGreaterEqual(filas["A"]["puntaje"], 2)
        self.assertEqual(filas["B"]["puntaje"], 1)

    @staticmethod
    def _fila(estudiante, periodo, carga, asistencia, cambio, alerta):
        return {
            "student_id": estudiante,
            "period_id": periodo,
            "credit_load": str(carga),
            "attendance_rate": str(asistencia),
            "grade_change": str(cambio),
            "dropout_alert": alerta,
        }


if __name__ == "__main__":
    unittest.main()
