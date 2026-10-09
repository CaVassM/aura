"""Agenda reservable que mantiene las citas y desencuentros en memoria (RAM)."""

from datetime import date, timedelta
from math import ceil
from pathlib import Path

from ..datos.modelos import cargar_csv, cargar_servicios
from ..motor.agenda import generar_agenda
from ..motor.datos import Cupo, Opcion, Servicio
from ..motor.reglas import precalcular_opciones
from .configuracion import cargar_yaml, ruta_data_pack


def _espera_media_d2(ruta: Path) -> float | None:
    """Espera media observada (`wait_days`) en D2, o None si el archivo no existe."""
    if not ruta.exists():
        return None
    esperas = [float(f["wait_days"]) for f in cargar_csv(ruta) if f.get("wait_days")]
    return sum(esperas) / len(esperas) if esperas else None


class AgendaViva:
    """Genera cupos reproducibles y mantiene reservas y desencuentros en RAM.

    El estado se pierde al reiniciar el proceso: no hay base de datos ni archivos.
    """

    def __init__(
        self,
        data_pack: Path | None = None,
        hoy: date | None = None,
        fraccion_liberada: float | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        semana_calendario: bool = False,
    ):
        self.parametros = cargar_yaml("parametros.yaml")
        self.tablas = cargar_yaml("tablas.yaml")
        self.hoy = hoy or date.fromisoformat(self.parametros["hoy"])
        ruta = data_pack or ruta_data_pack()
        self.ruta_data_pack = ruta
        self.servicios: list[Servicio] = cargar_servicios(ruta / "D6_services_map.geojson")
        self.espera_historica_dias = _espera_media_d2(ruta / "D2_support_services.csv")
        horizonte = int(self.parametros["horizonte_semanas"])
        self.ventana_dias = 7 * horizonte  # ventana de cada pedido: fecha + 1 … fecha + 14
        self.agenda_desde = desde or self.hoy + timedelta(days=1)
        self.agenda_hasta = hasta or self.hoy + timedelta(days=7 * horizonte)
        dias = (self.agenda_hasta - self.agenda_desde).days + 1
        self.ocupados_iniciales: set[str] = set()  # cupos que nacen ocupados (ocupación inicial)
        self.cupos, self.libres_base = generar_agenda(
            self.servicios,
            self.hoy,
            semanas=ceil(dias / 7),
            duracion_min=int(self.parametros["duracion_sesion_minutos"]),
            fraccion_liberada=float(
                self.parametros["fraccion_liberada"]
                if fraccion_liberada is None
                else fraccion_liberada
            ),
            ocupacion_inicial=float(self.parametros["ocupacion_inicial"]),
            semilla=42,
            dias_cerrados=set(),
            primer_dia=self.agenda_desde,
            ultimo_dia=self.agenda_hasta,
            semana_calendario=semana_calendario,
            ocupados_iniciales=self.ocupados_iniciales,
        )
        self.cupo_por_id = {cupo.id: cupo for cupo in self.cupos}
        self.servicio_por_id = {
            servicio.service_id: servicio for servicio in self.servicios
        }
        self.reservas: dict[str, dict] = {}
        self.siguiente_cita = 1
        self.desencuentros: list[dict] = []

    def cupos_ocupados(self) -> set[str]:
        """Incluye la ocupación inicial y las reservas vivas de esta agenda."""
        ocupados = set(self.cupo_por_id) - self.libres_base
        ocupados.update(cita["cupo_id"] for cita in self.reservas.values())
        return ocupados

    def libres_ahora(self) -> set[str]:
        """Cupos liberados para AURA y sin reserva viva."""
        return self.libres_base - {cita["cupo_id"] for cita in self.reservas.values()}

    def cupos_de_servicios(self, service_ids) -> set[str]:
        """Ids de todos los cupos de esos servicios (p. ej. para apartarlos de las propuestas directas)."""
        ids = set(service_ids)
        return {c.id for c in self.cupos if c.service_id in ids} if ids else set()

    def opciones_validas(
        self, solicitud, referencia: date | None = None
    ) -> tuple[Opcion, ...]:
        """Calcula opciones que respetan horario, afinidad, canal y distrito.

        La ventana de la solicitud va de `referencia` + 1 a `referencia` + `ventana_dias` días
        (la referencia es `hoy` por defecto); ningún cupo fuera de ella es una opción.
        """
        libres = self.libres_base - {cita["cupo_id"] for cita in self.reservas.values()}
        por_solicitud = precalcular_opciones(
            [solicitud],
            self.cupos,
            libres,
            referencia or self.hoy,
            float(self.parametros["beta"]),
            horizonte_dias=self.ventana_dias,
        )
        return por_solicitud[solicitud.id]

    def reservar(
        self,
        estudiante_id: str,
        opcion_id: str,
        fecha_solicitud: date | None = None,
        servicio_ideal: str | None = None,
    ) -> dict:
        """Verifica disponibilidad al reservar y guarda la cita en memoria.

        `fecha_solicitud` (por defecto, `hoy`) es la referencia: el cupo debe caer en su ventana
        (de la fecha + 1 a la fecha + `ventana_dias`). `servicio_ideal` (opcional) es el tipo que
        el pedido necesitaba: permite saber después si se atendió con una alternativa afín.
        """
        cupo_id, separador, canal = opcion_id.partition("|")
        ocupados = self.cupos_ocupados()
        cupo = self.cupo_por_id.get(cupo_id)
        if not separador or cupo is None or canal not in cupo.canales:
            return {
                "ok": False,
                "error": "opcion_invalida",
                "detalle": "El opcion_id debe ser uno de los que entregó proponer_opciones (`<cupo>|<canal>`)",
            }
        if cupo_id in ocupados:
            return {"ok": False, "error": "cupo_ya_tomado"}
        solicitada = fecha_solicitud or self.hoy
        if not solicitada < cupo.fecha <= solicitada + timedelta(days=self.ventana_dias):
            return {"ok": False, "error": "cupo_fuera_de_ventana"}
        cita_id = f"CITA-{self.siguiente_cita:07d}"
        self.siguiente_cita += 1
        cita = self._serializar_cita(
            cita_id, estudiante_id, cupo, canal, solicitada, servicio_ideal
        )
        self.reservas[cita_id] = cita
        return {"ok": True, "cita": cita}

    def cancelar(self, cita_id: str, estudiante_id: str | None = None) -> dict:
        """Libera una cita existente; una cita inexistente devuelve un error claro.

        Si se indica `estudiante_id`, solo su dueño puede cancelarla.
        """
        cita = self.reservas.get(cita_id)
        if cita is None or (estudiante_id and cita["estudiante_id"] != estudiante_id):
            return {"ok": False, "error": "cita_no_encontrada"}
        del self.reservas[cita_id]
        return {"ok": True, "cita_id": cita_id}

    def registrar_desencuentro(self, registro: dict) -> dict:
        """Agrega una solicitud sin opciones compatibles y le asigna un identificador."""
        registro_id = f"DES-{len(self.desencuentros) + 1:07d}"
        fila = {"registro_id": registro_id, **registro}
        self.desencuentros.append(fila)
        return fila

    def cupos_libres_de(self, service_id: str) -> list[Cupo]:
        """Cupos futuros aún libres de un servicio, ordenados por fecha y hora."""
        ocupados = self.cupos_ocupados()
        libres = [
            cupo
            for cupo in self.cupos
            if cupo.service_id == service_id
            and cupo.id not in ocupados
            and cupo.fecha > self.hoy
        ]
        return sorted(libres, key=lambda c: (c.fecha, c.hora_inicio))

    def _serializar_cita(
        self, cita_id, estudiante_id, cupo, canal, solicitada, servicio_ideal=None
    ) -> dict:
        """Construye el comprobante que se entrega al estudiante o al agente."""
        servicio = self.servicio_por_id[cupo.service_id]
        return {
            "cita_id": cita_id,
            "estudiante_id": estudiante_id,
            "cupo_id": cupo.id,
            "opcion_id": f"{cupo.id}|{canal}",
            "service_id": cupo.service_id,
            "servicio_nombre": servicio.nombre,
            "tipo": cupo.tipo,
            "distrito": cupo.distrito,
            "fecha": cupo.fecha.isoformat(),
            "hora_inicio": cupo.hora_inicio.isoformat(timespec="minutes"),
            "hora_fin": cupo.hora_fin.isoformat(timespec="minutes"),
            "canal": canal,
            "fecha_solicitud": solicitada.isoformat(),
            "dias_espera": (cupo.fecha - solicitada).days,
            "servicio_ideal": servicio_ideal,
            "es_alternativa": servicio_ideal is not None and servicio_ideal != cupo.tipo,
        }
