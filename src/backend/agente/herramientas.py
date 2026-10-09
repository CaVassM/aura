"""Herramientas LangChain del agente, creadas para cada mensaje.

Diferencias deliberadas con las herramientas del motor (`aura.herramientas`):
- El modelo NO elige el `estudiante_id`: sale de la sesión, así nadie reserva ni cancela a nombre de otra persona.
- `reservar_cita` solo acepta un `opcion_id` de la última propuesta de esta sesión (evita ids inventados).
- `registrar_desencuentro` no recibe argumentos: usa la última solicitud buscada.
- Las respuestas son JSON compacto y en español, listo para que el modelo lo redacte.
"""

import json
from dataclasses import dataclass, field
from datetime import date

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .prompt import DIAS_ES
from .puerto import PuertoAgenda
from .sesion import SesionChat


@dataclass
class EventoHerramienta:
    """Una llamada que hizo el modelo en este turno y lo que devolvió la plataforma."""

    nombre: str
    ok: bool
    resultado: dict


@dataclass
class ContextoTurno:
    sesion: SesionChat
    puerto: PuertoAgenda
    eventos: list[EventoHerramienta] = field(default_factory=list)


class FranjaArgs(BaseModel):
    dia: str = Field(description="Día en inglés abreviado: Mon, Tue, Wed, Thu, Fri, Sat o Sun")
    desde: str = Field(description="Hora de inicio HH:MM en 24 h, p. ej. 09:00")
    hasta: str = Field(description="Hora de fin HH:MM en 24 h, p. ej. 12:00")


class ProponerArgs(BaseModel):
    motivo: str = Field(
        description=(
            "Uno de: academic_pressure, sleep_and_routine, social_support, career_concern, "
            "preventive_guidance, service_navigation"
        )
    )
    franjas: list[FranjaArgs] = Field(min_length=1, description="Días y horas en que la persona puede asistir")
    canales_aceptables: list[str] = Field(
        min_length=1, description="Lista con uno o más de: digital (videollamada), phone (teléfono), in_person (presencial)"
    )
    distrito: str = Field(default="", description="Solo si la persona lo dijo y no estaba ya en los datos conocidos; si no, déjalo vacío")
    grupo: str = Field(default="", description="diurno o nocturno; solo si la persona lo dijo, si no déjalo vacío")
    k: int = Field(default=3, ge=1, le=5, description="Cuántas opciones buscar")


class ReservarArgs(BaseModel):
    opcion_id: str = Field(description="El `opcion_id` exacto de la opción que la persona eligió, p. ej. C0000123|digital")


class CancelarArgs(BaseModel):
    cita_id: str = Field(description="Número de cita, p. ej. CITA-0000001")


class SinArgs(BaseModel):
    pass


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False)


def _dia_es(fecha_iso: str) -> str:
    return DIAS_ES[date.fromisoformat(fecha_iso).weekday()]


def _opcion_para_modelo(o: dict) -> dict:
    return {
        "opcion_id": o["opcion_id"],
        "servicio": o["servicio_nombre"],
        "tipo": o.get("tipo_label", o["tipo"]),
        "distrito": o["distrito"],
        "fecha": o["fecha"],
        "dia_semana": o.get("dia_semana") or _dia_es(o["fecha"]),
        "hora_inicio": o["hora_inicio"],
        "hora_fin": o["hora_fin"],
        "canal": o.get("canal_label", o["canal"]),
        "es_alternativa": o["es_alternativa"],
        "dias_de_espera": o["dias_espera"],
    }


def _cita_para_modelo(c: dict) -> dict:
    return {
        "cita_id": c["id"],
        "servicio": c["servicio_nombre"],
        "tipo": c.get("tipo_label", c["tipo"]),
        "fecha": c["fecha"],
        "dia_semana": c.get("dia_semana") or _dia_es(c["fecha"]),
        "hora_inicio": c["hora_inicio"],
        "hora_fin": c["hora_fin"],
        "canal": c.get("canal_label", c["canal"]),
        "estado": c["estado"],
    }


def construir_herramientas(ctx: ContextoTurno) -> list[StructuredTool]:
    sesion, puerto = ctx.sesion, ctx.puerto

    def registrar(nombre: str, ok: bool, resultado: dict) -> None:
        ctx.eventos.append(EventoHerramienta(nombre, ok, resultado))

    def proponer_opciones(
        motivo: str,
        franjas: list[FranjaArgs],
        canales_aceptables: list[str],
        distrito: str = "",
        grupo: str = "",
        k: int = 3,
    ) -> str:
        distrito = distrito or sesion.contexto.distrito
        if not distrito:
            return _json({"ok": False, "error": "falta_distrito", "detalle": "Pregunta en qué distrito está la persona."})
        solicitud = {
            "estudiante_id": sesion.estudiante_id,
            "motivo": motivo,
            "distrito": distrito,
            "grupo": grupo or sesion.contexto.grupo or "diurno",
            "franjas": [f.model_dump() if isinstance(f, BaseModel) else f for f in franjas],
            "canales_aceptables": canales_aceptables,
        }
        resultado = puerto.proponer(solicitud, k)
        if resultado.get("motivo_vacio") == "solicitud_invalida":
            registrar("proponer_opciones", False, resultado)
            return _json({"ok": False, "error": "solicitud_invalida", "detalle": resultado.get("detalle", "")})
        sesion.ultima_solicitud = solicitud
        sesion.servicio_ideal = resultado.get("servicio_ideal")
        sesion.desencuentro_registrado = False
        sesion.propuestas = {o["opcion_id"]: o for o in resultado["opciones"]}
        registrar("proponer_opciones", True, resultado)
        if not resultado["opciones"]:
            return _json(
                {
                    "opciones": [],
                    "motivo_vacio": resultado.get("motivo_vacio", "sin_cupos_compatibles"),
                    "sugerencia": resultado.get(
                        "sugerencia",
                        "Ofrece ampliar días u horarios o aceptar otro canal; si no puede, registra el desencuentro.",
                    ),
                }
            )
        return _json({"opciones": [_opcion_para_modelo(o) for o in resultado["opciones"]]})

    def reservar_cita(opcion_id: str) -> str:
        opcion_id = opcion_id.strip()
        if opcion_id not in sesion.propuestas:
            # El modelo a veces omite el canal: si el cupo coincide con una sola opción, se usa esa.
            coincidencias = [i for i in sesion.propuestas if i.split("|")[0] == opcion_id.split("|")[0]]
            if len(coincidencias) == 1:
                opcion_id = coincidencias[0]
            else:
                resultado = {
                    "ok": False,
                    "error": "opcion_no_propuesta",
                    "detalle": "Ese opcion_id no está en las opciones que mostraste. Usa uno de la lista.",
                    "opcion_ids_validos": list(sesion.propuestas),
                }
                registrar("reservar_cita", False, resultado)
                return _json(resultado)
        resultado = puerto.reservar(sesion.estudiante_id, opcion_id, sesion.servicio_ideal)
        registrar("reservar_cita", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            if resultado.get("error") == "cupo_ya_tomado":
                sesion.propuestas.pop(opcion_id, None)
            return _json(
                {"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")}
            )
        sesion.propuestas = {}
        return _json({"ok": True, "cita": _cita_para_modelo(resultado["cita"])})

    def cancelar_cita(cita_id: str) -> str:
        resultado = puerto.cancelar(cita_id.strip(), sesion.estudiante_id)
        registrar("cancelar_cita", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            return _json(
                {"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")}
            )
        return _json({"ok": True, "cita": _cita_para_modelo(resultado["cita"])})

    def listar_mis_citas() -> str:
        citas = puerto.listar_citas(sesion.estudiante_id)
        registrar("listar_mis_citas", True, {"citas": citas})
        return _json({"citas": [_cita_para_modelo(c) for c in citas]})

    def registrar_desencuentro() -> str:
        if sesion.ultima_solicitud is None:
            return _json(
                {"ok": False, "error": "sin_busqueda_previa", "detalle": "Primero busca opciones con proponer_opciones."}
            )
        if sesion.desencuentro_registrado:
            return _json({"ok": True, "detalle": "Ya estaba registrado para esta búsqueda."})
        resultado = puerto.registrar_desencuentro(sesion.ultima_solicitud)
        registrar("registrar_desencuentro", bool(resultado.get("ok")), resultado)
        if resultado.get("ok"):
            sesion.desencuentro_registrado = True
        return _json(resultado)

    return [
        StructuredTool.from_function(
            func=proponer_opciones,
            name="proponer_opciones",
            description=(
                "Busca citas compatibles con lo que la persona necesita y devuelve hasta k opciones ordenadas "
                "de mejor a peor. No reserva nada. Úsala en cuanto tengas motivo, días/horas y canal."
            ),
            args_schema=ProponerArgs,
        ),
        StructuredTool.from_function(
            func=reservar_cita,
            name="reservar_cita",
            description=(
                "Reserva la opción que la persona eligió de la última lista mostrada. Úsala SOLO tras una elección "
                "clara. Devuelve el comprobante de la cita o un error."
            ),
            args_schema=ReservarArgs,
        ),
        StructuredTool.from_function(
            func=cancelar_cita,
            name="cancelar_cita",
            description="Cancela una cita de la persona y libera el cupo. Confirma con ella antes de usarla.",
            args_schema=CancelarArgs,
        ),
        StructuredTool.from_function(
            func=listar_mis_citas,
            name="listar_mis_citas",
            description="Lista las citas de la persona (número, fecha, hora, estado). Úsala para ver o cancelar citas.",
            args_schema=SinArgs,
        ),
        StructuredTool.from_function(
            func=registrar_desencuentro,
            name="registrar_desencuentro",
            description=(
                "Avisa al equipo de coordinación que la última búsqueda no tuvo ninguna opción que sirviera. "
                "Úsala solo cuando no hay opciones y la persona no puede cambiar días, horas ni canal, o rechazó todas."
            ),
            args_schema=SinArgs,
        ),
    ]
