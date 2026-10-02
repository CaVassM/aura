"""Agenda reservable que persiste las citas para sobrevivir a reinicios."""

from datetime import date, datetime
import json
from pathlib import Path

from ..datos.carga import cargar_data_pack
from ..motor.agenda import generar_agenda
from ..motor.datos import Cupo, Opcion, Servicio
from ..motor.reglas import precalcular_opciones
from .configuracion import RAIZ_PROYECTO, cargar_yaml, ruta_data_pack


class AgendaViva:
    """Genera cupos reproducibles y mantiene reservas en un JSON local."""

    def __init__(self, ruta_estado: Path | None = None, data_pack: Path | None = None):
        self.parametros = cargar_yaml("parametros.yaml")
        self.tablas = cargar_yaml("tablas.yaml")
        self.hoy = date.fromisoformat(self.parametros["hoy"])
        self.ruta_estado = (
            ruta_estado or RAIZ_PROYECTO / "salidas" / "estado_agenda.json"
        )
        datos = cargar_data_pack(data_pack or ruta_data_pack())
        self.servicios: list[Servicio] = datos["servicios"]
        self.cupos, self.libres_base = generar_agenda(
            self.servicios,
            self.hoy,
            semanas=int(self.parametros["horizonte_semanas"]),
            duracion_min=int(self.parametros["duracion_sesion_minutos"]),
            fraccion_liberada=float(self.parametros["fraccion_liberada"]),
            ocupacion_inicial=float(self.parametros["ocupacion_inicial"]),
            semilla=42,
            dias_cerrados=set(),
        )
        self.cupo_por_id = {cupo.id: cupo for cupo in self.cupos}
        self.servicio_por_id = {
            servicio.service_id: servicio for servicio in self.servicios
        }
        self.reservas: dict[str, dict] = {}
        self.siguiente_cita = 1
        self._cargar_estado()

    def _cargar_estado(self) -> None:
        """Restaura las reservas conocidas y conserva el contador de citas."""
        if not self.ruta_estado.exists():
            return
        estado = json.loads(self.ruta_estado.read_text(encoding="utf-8"))
        self.reservas = estado.get("reservas", {})
        self.siguiente_cita = int(estado.get("siguiente_cita", len(self.reservas) + 1))

    def _guardar_estado(self) -> None:
        """Escribe el estado serializable en UTF-8 para mantener citas entre sesiones."""
        self.ruta_estado.parent.mkdir(parents=True, exist_ok=True)
        estado = {"reservas": self.reservas, "siguiente_cita": self.siguiente_cita}
        self.ruta_estado.write_text(
            json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def cupos_ocupados(self) -> set[str]:
        """Incluye la ocupación inicial y las reservas vivas de esta agenda."""
        ocupados = set(self.cupo_por_id) - self.libres_base
        ocupados.update(cita["cupo_id"] for cita in self.reservas.values())
        return ocupados

    def opciones_validas(self, solicitud) -> tuple[Opcion, ...]:
        """Calcula opciones que respetan horario, afinidad, canal y distrito."""
        libres = self.libres_base - {cita["cupo_id"] for cita in self.reservas.values()}
        por_solicitud = precalcular_opciones(
            [solicitud], self.cupos, libres, self.hoy, float(self.parametros["beta"])
        )
        return por_solicitud[solicitud.id]

    def reservar(self, estudiante_id: str, opcion_id: str) -> dict:
        """Verifica disponibilidad al reservar y guarda la cita de forma persistente."""
        cupo_id, separador, canal = opcion_id.partition("|")
        ocupados = self.cupos_ocupados()
        cupo = self.cupo_por_id.get(cupo_id)
        if (
            not separador
            or cupo is None
            or cupo_id in ocupados
            or canal not in cupo.canales
        ):
            return {"ok": False, "error": "cupo_ya_tomado"}
        cita_id = f"CITA-{self.siguiente_cita:07d}"
        self.siguiente_cita += 1
        cita = self._serializar_cita(cita_id, estudiante_id, cupo, canal)
        self.reservas[cita_id] = cita
        self._guardar_estado()
        return {"ok": True, "cita": cita}

    def cancelar(self, cita_id: str) -> dict:
        """Libera una cita existente; una cita inexistente devuelve un error claro."""
        if cita_id not in self.reservas:
            return {"ok": False, "error": "cita_no_encontrada"}
        del self.reservas[cita_id]
        self._guardar_estado()
        return {"ok": True, "cita_id": cita_id}

    def _serializar_cita(self, cita_id, estudiante_id, cupo, canal) -> dict:
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
        }
