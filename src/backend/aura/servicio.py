"""Servicio del motor de asignación: único punto de entrada desde fuera del paquete `aura`.

La plataforma (`app/`) y el agente conversacional hablan con el motor solo a través
de esta fachada. Devuelve diccionarios JSON; no expone dataclasses ni la agenda interna.
Todo el estado vive en RAM dentro de la instancia.
"""

from datetime import timedelta

from .datos.modelos import Solicitud, cargar_csv
from .herramientas.esquemas import esquemas_herramientas
from .herramientas.estado_agenda import AgendaViva
from .herramientas.herramientas import HerramientasAgente
from .motor.baselines import escalar_demanda, orden_llegada, simular_solicitudes


class ServicioAsignacion:
    """Motor de asignación y herramientas del agente sobre una agenda en memoria."""

    def __init__(self, agenda: AgendaViva | None = None, **opciones_agenda):
        """`opciones_agenda` (hoy, fraccion_liberada, data_pack) se pasan a la agenda nueva."""
        self._agenda = agenda or AgendaViva(**opciones_agenda)
        self._herramientas = HerramientasAgente(self._agenda)

    # --- Herramientas del agente (ver docs/contrato_herramientas.md) ---

    def esquemas_herramientas(self) -> list[dict]:
        """Declaraciones name/description/parameters para el tool calling de un LLM."""
        distritos = sorted({s.distrito for s in self._agenda.servicios})
        return esquemas_herramientas(distritos, list(self._agenda.tablas["motivo_a_servicio"]))

    def ejecutar_herramienta(self, nombre: str, argumentos: dict | str | None) -> dict:
        """Ejecuta una llamada de herramienta tal como la emite el LLM."""
        return self._herramientas.ejecutar(nombre, argumentos)

    def proponer_opciones(self, solicitud: dict, k: int = 3) -> dict:
        """Hasta k propuestas válidas, sin reservarlas."""
        return self._herramientas.proponer_opciones(solicitud, k)

    def reservar(
        self, estudiante_id: str, opcion_id: str, servicio_ideal: str | None = None
    ) -> dict:
        """Reserva la opción si su cupo sigue libre."""
        return self._herramientas.reservar(estudiante_id, opcion_id, servicio_ideal)

    def cancelar_cita(self, cita_id: str, estudiante_id: str | None = None) -> dict:
        """Cancela una cita y libera su cupo (con `estudiante_id`, solo su dueño puede)."""
        return self._herramientas.cancelar_cita(cita_id, estudiante_id)

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        """Registra en RAM una solicitud sin opción compatible."""
        return self._herramientas.registrar_desencuentro(solicitud)

    def atender(self, solicitud: Solicitud) -> dict:
        """Modo directo para una solicitud ya modelada: reserva (k=1) o registra desencuentro."""
        return self._herramientas.atender(solicitud)

    def demanda_demo(self, semilla: int, factor: float) -> list[Solicitud]:
        """Semana mediana de D2 convertida en solicitudes (sin D1) y escalada por `factor`.

        Cada pedido conserva el día de la semana de su fila en D2 y queda fechado dentro de
        la semana de `hoy` (lunes a domingo); `simular_solicitudes` fecha en la semana previa
        a la fecha base, por eso se le pasa una semana después.
        """
        d2 = cargar_csv(self._agenda.ruta_data_pack / "D2_support_services.csv")
        base, _ = simular_solicitudes(
            d2, [], self._agenda.hoy + timedelta(days=7), semilla
        )
        return escalar_demanda(base, factor, semilla)

    def atender_lote(self, solicitudes: list[Solicitud]) -> list[dict]:
        """Atiende las solicitudes en orden de llegada (modo directo, k=1)."""
        por_id = {s.id: s for s in solicitudes}
        return [self.atender(por_id[i]) for i in orden_llegada(solicitudes)]

    # --- Consultas de solo lectura para la plataforma ---

    def servicios(self) -> list[dict]:
        """Servicios de la red con su tipo, distrito y canales."""
        return [
            {
                "service_id": s.service_id,
                "nombre": s.nombre,
                "tipo": s.tipo,
                "distrito": s.distrito,
                "canales": list(s.canales),
                "capacidad_semanal": s.capacidad_semanal,
                "horario": [
                    {
                        "dia": dia,
                        "desde": desde.isoformat(timespec="minutes"),
                        "hasta": hasta.isoformat(timespec="minutes"),
                    }
                    for dia, desde, hasta in s.dias_horas
                ],
            }
            for s in self._agenda.servicios
        ]

    def servicio(self, service_id: str) -> dict | None:
        """Un servicio por identificador, o None si no existe."""
        return next((s for s in self.servicios() if s["service_id"] == service_id), None)

    def cupos_libres(self, service_id: str) -> list[dict]:
        """Cupos futuros libres de un servicio, ordenados cronológicamente."""
        return [
            {
                "cupo_id": c.id,
                "service_id": c.service_id,
                "fecha": c.fecha.isoformat(),
                "hora_inicio": c.hora_inicio.isoformat(timespec="minutes"),
                "hora_fin": c.hora_fin.isoformat(timespec="minutes"),
                "canales": list(c.canales),
            }
            for c in self._agenda.cupos_libres_de(service_id)
        ]

    def citas(self) -> list[dict]:
        """Comprobantes de las citas vivas."""
        return list(self._agenda.reservas.values())

    def desencuentros(self) -> list[dict]:
        """Solicitudes registradas sin opciones compatibles."""
        return list(self._agenda.desencuentros)

    def espera_historica_dias(self) -> float | None:
        """Espera media observada en D2 (`wait_days`), o None si D2 no está disponible."""
        return self._agenda.espera_historica_dias

    def inventario_cupos(self) -> list[dict]:
        """Todos los cupos de la agenda con su estado: ocupado desde el inicio, liberado para AURA, reservado."""
        agenda = self._agenda
        reservados = {cita["cupo_id"] for cita in agenda.reservas.values()}
        return [
            {
                "cupo_id": c.id,
                "service_id": c.service_id,
                "fecha": c.fecha.isoformat(),
                "ocupado_inicial": c.id in agenda.ocupados_iniciales,
                "liberado": c.id in agenda.libres_base,
                "reservado": c.id in reservados,
            }
            for c in agenda.cupos
        ]

    def cupos_liberados(self, service_id: str | None = None) -> list[dict]:
        """Cupos liberados (de todos los servicios o de uno), con su fecha y si hay una cita."""
        agenda = self._agenda
        ocupados = {cita["cupo_id"] for cita in agenda.reservas.values()}
        cupos = [
            c
            for c in agenda.cupos
            if c.id in agenda.libres_base
            and (service_id is None or c.service_id == service_id)
        ]
        return [
            {
                "cupo_id": c.id,
                "service_id": c.service_id,
                "fecha": c.fecha.isoformat(),
                "reservado": c.id in ocupados,
            }
            for c in sorted(cupos, key=lambda c: (c.fecha, c.hora_inicio, c.id))
        ]
