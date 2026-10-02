"""Implementación de las cuatro funciones que el agente puede invocar."""

import csv
from datetime import date, time
from pathlib import Path

from ..motor.datos import Franja, Solicitud
from ..motor.costo import mejores_opciones
from .configuracion import RAIZ_PROYECTO, cargar_yaml
from .estado_agenda import AgendaViva

_AGENDA: AgendaViva | None = None
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


def _agenda() -> AgendaViva:
    """Inicializa la agenda solo cuando se invoca una herramienta por primera vez."""
    global _AGENDA
    if _AGENDA is None:
        _AGENDA = AgendaViva()
    return _AGENDA


def _convertir_solicitud(entrada: dict) -> tuple[Solicitud, str]:
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
        date.fromisoformat(entrada.get("fecha_solicitud", _agenda().hoy.isoformat())),
        str(entrada.get("grupo", "diurno")),
    )
    return solicitud, tipo_ideal


def proponer_opciones(solicitud: dict, k: int = 3) -> dict:
    """Devuelve hasta k propuestas válidas y disponibles, sin reservarlas."""
    try:
        modelo, tipo_ideal = _convertir_solicitud(solicitud)
    except (KeyError, ValueError) as error:
        return {
            "opciones": [],
            "motivo_vacio": "solicitud_invalida",
            "detalle": str(error),
        }
    agenda = _agenda()
    validas = agenda.opciones_validas(modelo)
    ocupados = agenda.cupos_ocupados()
    mejores = mejores_opciones(
        modelo,
        validas,
        ocupados,
        max(0, int(k)),
        cupos_por_id=agenda.cupo_por_id,
        hoy=agenda.hoy,
        beta=float(agenda.parametros["beta"]),
    )
    if not mejores:
        return {
            "opciones": [],
            "motivo_vacio": "sin_cupos_compatibles",
            "servicio_ideal": tipo_ideal,
        }
    opciones = [_formatear_opcion(agenda, opcion, tipo_ideal) for opcion in mejores]
    return {"opciones": opciones, "servicio_ideal": tipo_ideal}


def _formatear_opcion(agenda: AgendaViva, opcion, tipo_ideal: str) -> dict:
    """Convierte el par cupo-canal a una respuesta JSON clara para tool calling."""
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


def reservar(estudiante_id: str, opcion_id: str) -> dict:
    """Toma un cupo si todavía está libre y persiste el comprobante de cita."""
    return _agenda().reservar(estudiante_id, opcion_id)


def cancelar_cita(cita_id: str) -> dict:
    """Cancela una cita viva y vuelve a liberar su cupo."""
    return _agenda().cancelar(cita_id)


def registrar_desencuentro(solicitud: dict) -> dict:
    """Guarda una solicitud sin opciones compatibles para su análisis operativo."""
    try:
        modelo, _ = _convertir_solicitud(solicitud)
    except (KeyError, ValueError) as error:
        return {"ok": False, "error": "solicitud_invalida", "detalle": str(error)}
    ruta = RAIZ_PROYECTO / "salidas" / "desencuentros_vivos.csv"
    existe = ruta.exists()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if existe:
        with ruta.open(encoding="utf-8") as lectura:
            numero_registro = sum(1 for _ in lectura)
    else:
        numero_registro = 1
    with ruta.open("a", encoding="utf-8", newline="") as archivo:
        campos = [
            "registro_id",
            "estudiante_id",
            "servicio_ideal",
            "franjas",
            "distrito",
            "grupo",
            "fecha",
        ]
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if not existe:
            escritor.writeheader()
        registro_id = f"DES-{numero_registro:07d}"
        escritor.writerow(
            {
                "registro_id": registro_id,
                "estudiante_id": modelo.id,
                "servicio_ideal": modelo.servicio_ideal,
                "franjas": ";".join(
                    f"{f.dia_semana}:{f.hora_inicio}-{f.hora_fin}"
                    for f in modelo.franjas
                ),
                "distrito": modelo.distrito,
                "grupo": modelo.grupo,
                "fecha": modelo.fecha_solicitud.isoformat(),
            }
        )
    return {"ok": True, "registro_id": registro_id}
