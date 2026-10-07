"""Implementación de las cuatro funciones que el agente puede invocar."""

from datetime import date, time

from ..motor.datos import Franja, Solicitud
from ..motor.costo import mejores_opciones
from .configuracion import cargar_yaml
from .estado_agenda import AgendaViva

_DIAS = {
    "mon": 0,
    "monday": 0,
    "lun": 0,
    "lunes": 0,
    "tue": 1,
    "tuesday": 1,
    "mar": 1,
    "martes": 1,
    "wed": 2,
    "wednesday": 2,
    "mie": 2,
    "miércoles": 2,
    "miercoles": 2,
    "thu": 3,
    "thursday": 3,
    "jue": 3,
    "jueves": 3,
    "fri": 4,
    "friday": 4,
    "vie": 4,
    "viernes": 4,
    "sat": 5,
    "saturday": 5,
    "sab": 5,
    "sábado": 5,
    "sabado": 5,
    "sun": 6,
    "sunday": 6,
    "dom": 6,
    "domingo": 6,
}


class HerramientasAgente:
    """Las cuatro herramientas del agente, sobre una agenda en RAM inyectada."""

    def __init__(self, agenda: AgendaViva | None = None):
        self.agenda = agenda or AgendaViva()

    def ejecutar(self, nombre: str, argumentos: dict) -> dict:
        """Despacha una llamada de tool calling por nombre; los errores se devuelven como JSON."""
        accion = {
            "proponer_opciones": self.proponer_opciones,
            "reservar": self.reservar,
            "cancelar_cita": self.cancelar_cita,
            "registrar_desencuentro": self.registrar_desencuentro,
        }.get(nombre)
        if accion is None:
            return {"ok": False, "error": "herramienta_desconocida", "detalle": nombre}
        try:
            return accion(**argumentos)
        except TypeError as error:
            return {"ok": False, "error": "argumentos_invalidos", "detalle": str(error)}

    def convertir_solicitud(self, entrada: dict) -> tuple[Solicitud, str]:
        """Valida preferencias JSON y traduce el motivo usando tablas.yaml."""
        return _convertir_solicitud(entrada, self.agenda.hoy)

    def proponer_opciones(self, solicitud: dict, k: int = 3) -> dict:
        """Devuelve hasta k propuestas válidas y disponibles, sin reservarlas."""
        try:
            modelo, tipo_ideal = self.convertir_solicitud(solicitud)
        except (KeyError, ValueError) as error:
            return {
                "opciones": [],
                "motivo_vacio": "solicitud_invalida",
                "detalle": str(error),
            }
        mejores = self._mejores(modelo, k)
        if not mejores:
            return {
                "opciones": [],
                "motivo_vacio": "sin_cupos_compatibles",
                "servicio_ideal": tipo_ideal,
            }
        opciones = [self._formatear_opcion(op, tipo_ideal) for op in mejores]
        return {"opciones": opciones, "servicio_ideal": tipo_ideal}

    def _mejores(self, modelo: Solicitud, k: int, referencia: date | None = None) -> list:
        """Hasta k opciones válidas y libres de menor costo para la solicitud.

        `referencia` es la fecha desde la cual se cuentan cupos y espera (por defecto, hoy).
        """
        agenda = self.agenda
        referencia = referencia or agenda.hoy
        return mejores_opciones(
            modelo,
            agenda.opciones_validas(modelo, referencia),
            agenda.cupos_ocupados(),
            max(0, int(k)),
            cupos_por_id=agenda.cupo_por_id,
            hoy=referencia,
            beta=float(agenda.parametros["beta"]),
        )

    def atender(self, solicitud: Solicitud) -> dict:
        """Modo directo: reserva la mejor opción (k=1) o registra un desencuentro.

        La referencia es la fecha de la propia solicitud: solo toma cupos posteriores a ella
        y su espera es `fecha_cupo − fecha_solicitud`.
        """
        referencia = solicitud.fecha_solicitud
        mejores = self._mejores(solicitud, 1, referencia)
        if not mejores:
            fila = self.agenda.registrar_desencuentro(self._registro(solicitud))
            return {"estado": "desencuentro", "registro_id": fila["registro_id"]}
        opcion = mejores[0]
        reserva = self.agenda.reservar(
            solicitud.id,
            f"{opcion.cupo_id}|{opcion.canal}",
            referencia,
            solicitud.servicio_ideal,
        )
        if not reserva["ok"]:
            return {"estado": reserva["error"]}
        return {"estado": "reservada", "cita": reserva["cita"]}

    def _formatear_opcion(self, opcion, tipo_ideal: str) -> dict:
        """Convierte el par cupo-canal a una respuesta JSON clara para tool calling."""
        agenda = self.agenda
        cupo = agenda.cupo_por_id[opcion.cupo_id]
        servicio = agenda.servicio_por_id[cupo.service_id]
        return {
            "opcion_id": f"{cupo.id}|{opcion.canal}",
            "service_id": cupo.service_id,
            "servicio_nombre": servicio.nombre,
            "tipo": cupo.tipo,
            "distrito": cupo.distrito,
            "fecha": cupo.fecha.isoformat(),
            "hora_inicio": cupo.hora_inicio.isoformat(timespec="minutes"),
            "hora_fin": cupo.hora_fin.isoformat(timespec="minutes"),
            "canal": opcion.canal,
            "dias_espera": (cupo.fecha - agenda.hoy).days,
            "es_alternativa": cupo.tipo != tipo_ideal,
            "afinidad": opcion.afinidad,
        }

    def reservar(
        self, estudiante_id: str, opcion_id: str, servicio_ideal: str | None = None
    ) -> dict:
        """Toma un cupo si todavía está libre y guarda el comprobante de cita en RAM.

        `servicio_ideal` (el `servicio_ideal` de la propuesta) es opcional.
        """
        return self.agenda.reservar(estudiante_id, opcion_id, servicio_ideal=servicio_ideal)

    def cancelar_cita(self, cita_id: str) -> dict:
        """Cancela una cita viva y vuelve a liberar su cupo."""
        return self.agenda.cancelar(cita_id)

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        """Guarda en RAM una solicitud sin opciones compatibles para su análisis operativo."""
        try:
            modelo, _ = self.convertir_solicitud(solicitud)
        except (KeyError, ValueError) as error:
            return {"ok": False, "error": "solicitud_invalida", "detalle": str(error)}
        fila = self.agenda.registrar_desencuentro(self._registro(modelo))
        return {"ok": True, "registro_id": fila["registro_id"]}

    @staticmethod
    def _registro(modelo: Solicitud) -> dict:
        """Datos de la solicitud que se conservan como desencuentro."""
        return {
            "estudiante_id": modelo.id,
            "motivo": modelo.motivo,
            "servicio_ideal": modelo.servicio_ideal,
            "franjas": [
                {
                    "dia_semana": f.dia_semana,
                    "desde": f.hora_inicio.isoformat(timespec="minutes"),
                    "hasta": f.hora_fin.isoformat(timespec="minutes"),
                }
                for f in modelo.franjas
            ],
            "canales_aceptables": list(modelo.canales_aceptables),
            "distrito": modelo.distrito,
            "grupo": modelo.grupo,
            "fecha": modelo.fecha_solicitud.isoformat(),
        }


def _convertir_solicitud(entrada: dict, hoy: date) -> tuple[Solicitud, str]:
    """Valida preferencias JSON y traduce el motivo usando tablas.yaml."""
    tablas = cargar_yaml("tablas.yaml")
    motivo = str(entrada.get("motivo", "")).strip()
    tipo_ideal = tablas["motivo_a_servicio"].get(motivo)
    if tipo_ideal is None:
        raise ValueError(f"Motivo no configurado: {motivo}")
    franjas = []
    for franja in entrada.get("franjas", []):
        dia = franja["dia"]
        indice = int(dia) if str(dia).isdigit() else _DIAS[str(dia).lower()]
        franjas.append(
            Franja(
                indice,
                time.fromisoformat(franja["desde"]),
                time.fromisoformat(franja["hasta"]),
            )
        )
    if not franjas:
        raise ValueError("La solicitud debe incluir al menos una franja horaria")
    solicitud = Solicitud(
        str(entrada["estudiante_id"]),
        tipo_ideal,
        str(entrada["distrito"]),
        tuple(franjas),
        tuple(entrada["canales_aceptables"]),
        date.fromisoformat(entrada.get("fecha_solicitud", hoy.isoformat())),
        str(entrada.get("grupo", "diurno")),
        motivo,
    )
    return solicitud, tipo_ideal
