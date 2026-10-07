"""Pruebas mínimas pedidas para invariantes del motor y el mini-ejemplo."""

import unittest
from datetime import date, time
from aura.datos.modelos import Cupo, Solicitud, Servicio, Franja, Opcion
from aura.motor.genetico import cruce_ox, genetico, enumerar
from aura.motor.fitness import decodificar, metricas
from aura.motor.baselines import z_plan_b
from aura.motor.reglas import vectorizar_opciones


class MotorTests(unittest.TestCase):
    def test_ox_no_repite_ni_pierde_elementos(self):
        a = list("ABCDEFG")
        b = list("GFEDCBA")
        for semilla in range(30):
            import random

            h1, h2 = cruce_ox(a, b, random.Random(semilla))
            self.assertEqual(set(h1), set(a))
            self.assertEqual(len(h1), len(set(h1)))
            self.assertEqual(set(h2), set(a))
            self.assertEqual(len(h2), len(set(h2)))

    def test_decodificador_no_duplica_cupo(self):
        c = Cupo(
            "C1",
            "S1",
            "counseling",
            "D",
            date(2026, 10, 2),
            time(9),
            time(10),
            ("digital",),
        )
        f = (Franja(4, time(9), time(11)),)
        ss = [
            Solicitud(
                x, "counseling", "D", f, ("digital",), date(2026, 10, 1), "diurno"
            )
            for x in ("A", "B")
        ]
        op = {x.id: (Opcion("C1", "digital", 1.0),) for x in ss}
        asign, fallidas = decodificar(["A", "B"], ss, op, [c], hoy=date(2026, 10, 1))
        vec, indice = vectorizar_opciones(op, [c])
        if vec is not None:
            asign_vec, fallidas_vec = decodificar(
                ["A", "B"],
                ss,
                op,
                [c],
                hoy=date(2026, 10, 1),
                opciones_ordenadas=True,
                opciones_vector=vec,
                indice_vector=indice,
            )
            self.assertEqual(asign_vec, asign)
            self.assertEqual(fallidas_vec, fallidas)
        self.assertEqual(len(asign), 1)
        self.assertEqual(len(fallidas), 1)
        self.assertEqual(len({v[0].id for v in asign.values()}), len(asign))

    def test_mini_ejemplo_premia_atender_a_todos(self):
        # Tres cupos counseling por la tarde, dos peer_support por la noche.
        dias = [1, 3, 4, 2, 5]
        horas = [(15, 16)] * 3 + [(19, 20)] * 2
        cupos = [
            Cupo(
                f"C{i}",
                "S1" if i < 3 else "S2",
                "counseling" if i < 3 else "peer_support",
                "D",
                date(2026, 10, 5 + d),
                time(h[0]),
                time(h[1]),
                ("digital",),
            )
            for i, (d, h) in enumerate(zip(dias, horas))
        ]
        tarde = (
            Franja(1, time(14), time(17)),
            Franja(3, time(14), time(17)),
            Franja(4, time(14), time(17)),
        )
        noche = (Franja(2, time(19), time(21)), Franja(5, time(19), time(21)))
        flex = tarde + noche
        specs = [
            ("Ana", "counseling", tarde),
            ("Beto", "counseling", tarde),
            ("Caro", "peer_support", noche),
            ("Diego", "peer_support", noche),
            ("Elena", "peer_support", flex),
        ]
        ss = [
            Solicitud(n, ideal, "D", fr, ("digital",), date(2026, 10, 1), "diurno")
            for n, ideal, fr in specs
        ]
        opciones = {}
        for s in ss:
            valid = []
            for c in cupos:
                afin = 1.0 if c.tipo == s.servicio_ideal else 0.6
                if any(
                    f.dia_semana == c.fecha.weekday()
                    and f.hora_inicio <= c.hora_inicio
                    and c.hora_fin <= f.hora_fin
                    for f in s.franjas
                ):
                    valid.append(Opcion(c.id, "digital", afin))
            opciones[s.id] = tuple(valid)
        hoy = date(2026, 10, 1)
        servicios = [
            Servicio("S1", "counseling", "D", (), 3, ("digital",)),
            Servicio("S2", "peer_support", "D", (), 2, ("digital",)),
        ]

        def medir(orden):
            asign, fallidas = decodificar(orden, ss, opciones, cupos, hoy=hoy)
            return metricas(asign, fallidas, ss, servicios, {"S1": 3, "S2": 2}, hoy, 14)

        z1 = lambda orden: medir(orden)["Z1"]
        # Elena primero prefiere un cupo nocturno de afinidad 1.0; Diego queda fuera.
        self.assertEqual(z1(["Elena", "Ana", "Beto", "Caro", "Diego"]), 1)
        # Protegiendo las necesidades más específicas, el decodificador asigna a todos.
        self.assertEqual(z1(["Ana", "Beto", "Caro", "Diego", "Elena"]), 0)
        z_completo = z_plan_b(medir(["Ana", "Beto", "Caro", "Diego", "Elena"]), 5, 14)
        z_falla = z_plan_b(medir(["Elena", "Ana", "Beto", "Caro", "Diego"]), 5, 14)
        self.assertLess(z_completo, z_falla)
        # La comprobación genética se hace sobre el Z total del plan B, no solo Z1.
        z_total = lambda orden: z_plan_b(medir(orden), 5, 14)
        exacto, z_exacto = enumerar([s.id for s in ss], z_total)
        _, z_ga, _ = genetico(
            [s.id for s in ss], z_total, poblacion=30, generaciones=50, semilla=42
        )
        self.assertAlmostEqual(z_ga, z_exacto)


if __name__ == "__main__":
    unittest.main()


class AgendaCalendarioTests(unittest.TestCase):
    """La capacidad semanal se reparte por semana Lun-Dom, proporcional si la semana queda cortada."""

    def setUp(self):
        from datetime import date, time
        from aura.motor.agenda import generar_agenda

        # Atiende de lunes a viernes, capacidad 50 por semana.
        horario = tuple((d, time(9), time(18)) for d in range(5))
        servicio = Servicio("S1", "counseling", "D1", horario, 50, ("digital",))
        # Rango: martes 10 a domingo 29 de noviembre de 2026 (semanas 9-15 cortada, 16-22 y 23-29).
        self.cupos, _ = generar_agenda(
            [servicio], date(2026, 11, 15), fraccion_liberada=1.0, ocupacion_inicial=0.0,
            primer_dia=date(2026, 11, 10), ultimo_dia=date(2026, 11, 29), semana_calendario=True,
        )

    def test_semana_cortada_recibe_capacidad_proporcional(self):
        from datetime import date

        por_semana = {}
        for c in self.cupos:
            lunes = c.fecha.toordinal() - c.fecha.weekday()
            por_semana[lunes] = por_semana.get(lunes, 0) + 1
        primera, segunda, tercera = (por_semana[k] for k in sorted(por_semana))
        self.assertEqual((segunda, tercera), (50, 50))
        self.assertEqual(primera, round(50 * 4 / 5))  # martes a viernes: 4 de 5 días de atención
        self.assertEqual(min(c.fecha for c in self.cupos), date(2026, 11, 10))
        self.assertEqual(max(c.fecha for c in self.cupos), date(2026, 11, 27))
