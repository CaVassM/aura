"""Herramientas LangChain del agente, creadas para cada mensaje.

Diferencias deliberadas con las herramientas del motor (`aura.herramientas`):
- El modelo NO elige el `estudiante_id`: sale de la sesión, así nadie reserva ni cancela a nombre de otra persona.
- `reservar_cita` recibe el NÚMERO de la opción elegida (1, 2, 3…) de la última lista; el modelo nunca ve ni copia
  identificadores internos, así que no puede inventarlos ni mostrárselos a la persona.
- `proponer_opciones` se niega a buscar si la persona no ha dicho días ni canal, y `cancelar_cita` se niega si la
  persona no pidió cancelar ni confirmó una pregunta de cancelar (ver `entrada.py`).
- `registrar_desencuentro` no recibe argumentos: usa la última solicitud buscada.
- Las respuestas son JSON compacto y en español, listo para que el modelo lo redacte.
"""

import json
from dataclasses import dataclass, field
from datetime import date

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from . import entrada
from .prompt import DIAS_ES, MESES_ES
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
    mensaje: str = ""  # el mensaje que se está respondiendo (aún no está en sesion.mensajes)
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
    numero: int = Field(ge=1, description="Número de la opción que la persona eligió en la última lista (1, 2, 3…)")


class CancelarArgs(BaseModel):
    cita_id: str = Field(description="Número de cita, p. ej. CITA-0000001")


class SinArgs(BaseModel):
    pass


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False)


def _dia_es(fecha_iso: str) -> str:
    return DIAS_ES[date.fromisoformat(fecha_iso).weekday()]


def _fecha_texto(fecha_iso: str) -> str:
    f = date.fromisoformat(fecha_iso)
    return f"{DIAS_ES[f.weekday()]} {f.day} de {MESES_ES[f.month - 1]}"


def _opcion_para_modelo(numero: int, o: dict) -> dict:
    canal = o.get("canal_label", o["canal"])
    tipo = o.get("tipo_label", o["tipo"])
    texto = f"{o['servicio_nombre']} ({tipo}) · {_fecha_texto(o['fecha'])}, de {o['hora_inicio']} a {o['hora_fin']} · {canal}"
    if o["es_alternativa"]:
        texto += " · servicio distinto al ideal, pero compatible"
    return {"numero": numero, "texto": texto, "distrito": o["distrito"], "dias_de_espera": o["dias_espera"]}


def _cita_para_modelo(c: dict) -> dict:
    canal = c.get("canal_label", c["canal"])
    return {
        "cita_id": c["id"],
        "texto": f"{c['servicio_nombre']} ({c.get('tipo_label', c['tipo'])}) · {_fecha_texto(c['fecha'])}, "
        f"de {c['hora_inicio']} a {c['hora_fin']} · {canal}",
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
        textos = [m.content for m in sesion.mensajes if m.type == "human" and isinstance(m.content, str)]
        faltan = entrada.faltantes(textos + [ctx.mensaje])
        if faltan:
            resultado = {
                "ok": False,
                "error": "faltan_datos",
                "detalle": "La persona todavía no dijo " + " ni ".join(faltan) + ". Pregúntaselo; no los inventes ni busques todavía.",
            }
            registrar("proponer_opciones", False, resultado)
            return _json(resultado)
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
        return _json(
            {
                "opciones": [_opcion_para_modelo(i, o) for i, o in enumerate(resultado["opciones"], 1)],
                "indicacion": "Muestra cada opción con su `texto`, numeradas, y pregunta cuál prefiere.",
            }
        )

    def reservar_cita(numero: int) -> str:
        opciones = list(sesion.propuestas.values())
        if not 1 <= numero <= len(opciones):
            resultado = {
                "ok": False,
                "error": "opcion_no_propuesta",
                "detalle": f"No hay una opción {numero} en la última lista"
                + (f" (van del 1 al {len(opciones)})." if opciones else "; primero busca opciones con proponer_opciones."),
            }
            registrar("reservar_cita", False, resultado)
            return _json(resultado)
        opcion_id = opciones[numero - 1]["opcion_id"]
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
        ultima = next(
            (m.content for m in reversed(sesion.mensajes)
             if m.type == "ai" and isinstance(m.content, str) and m.content and not getattr(m, "tool_calls", None)),
            "",
        )
        if not entrada.confirma_cancelacion(ctx.mensaje, ultima):
            resultado = {
                "ok": False,
                "error": "falta_confirmacion",
                "detalle": "La persona no pidió cancelar la cita. Pregúntale si quiere que la cancelen y espera su respuesta.",
            }
            registrar("cancelar_cita", False, resultado)
            return _json(resultado)
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
                "Reserva la opción que la persona eligió de la última lista mostrada, por su número. Úsala SOLO tras "
                "una elección clara. Devuelve el comprobante de la cita o un error."
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
