"""Herramientas LangChain del agente, creadas para cada mensaje.

Diferencias deliberadas con las herramientas del motor (`aura.herramientas`):
- El modelo NO elige el `estudiante_id`: sale de la sesión, así nadie reserva ni cancela a nombre de otra persona.
- `reservar_cita` recibe el NÚMERO de la opción elegida (1, 2, 3…) de la última lista; el modelo nunca ve ni copia
  identificadores internos, así que no puede inventarlos ni mostrárselos a la persona.
- `proponer_opciones` se niega a buscar si la persona no ha dicho días ni canal, y `cancelar_cita` se niega si la
  persona no pidió cancelar ni confirmó una pregunta de cancelar (ver `entrada.py`).
- `registrar_desencuentro` y `entrar_a_lote` no reciben argumentos: usan la última solicitud buscada.
- Las respuestas son JSON compacto y en español, listo para que el modelo lo redacte.
"""

import json
import unicodedata
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
    distrito: str = Field(
        default="",
        description=(
            "Solo si la persona dijo que irá a otro distrito distinto al de su perfil. Uno de: DIST_GAIA, "
            "DIST_NEBULA, DIST_VECTOR, DIST_HORIZON, DIST_QUANTUM. Si no, déjalo vacío"
        ),
    )
    grupo: str = Field(
        default="",
        description=(
            "diurno o nocturno: el turno en que ESTUDIA la persona. Solo si ella lo dijo (p. ej. «estudio de noche»); "
            "si no lo dijo, déjalo vacío y no se lo preguntes"
        ),
    )
    k: int = Field(default=3, ge=1, le=5, description="Cuántas opciones buscar")


class ReservarArgs(BaseModel):
    numero: int = Field(ge=1, description="Número de la opción que la persona eligió en la última lista (1, 2, 3…)")


class CancelarArgs(BaseModel):
    cita_id: str = Field(description="Número de cita, p. ej. CITA-0000001")


class SinArgs(BaseModel):
    pass


def _grupo(valor: str) -> str | None:
    """Normaliza lo que el modelo captura del turno de estudio; None si no es reconocible."""
    v = valor.strip().lower()
    if v in {"nocturno", "noche", "night", "evening", "vespertino", "nocturna"}:
        return "nocturno"
    if v in {"diurno", "dia", "día", "day", "mañana", "diurna"}:
        return "diurno"
    return None


def _distrito_codigo(valor: str) -> str:
    """«Nébula», «nebula» o «DIST_NEBULA» → `DIST_NEBULA` (el motor valida que exista)."""
    base = unicodedata.normalize("NFD", valor.strip().lower())
    texto = "".join(c for c in base if unicodedata.category(c) != "Mn").upper().replace(" ", "_")
    return texto if texto.startswith("DIST_") else f"DIST_{texto}"


def _grupo_por_horas(franjas: list[dict]) -> str:
    """Sin dato explícito: si todo lo que puede es de 18:00 en adelante, se asume turno nocturno."""
    return "nocturno" if franjas and all(f["desde"].strip()[:2].isdigit() and int(f["desde"].strip()[:2]) >= 18 for f in franjas) else "diurno"


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False)


def _pct(tasa: float) -> str:
    return f"{round(100 * tasa)} %"


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
        distrito = _distrito_codigo(distrito) if distrito.strip() else sesion.contexto.distrito
        if not distrito:
            return _json({"ok": False, "error": "falta_distrito", "detalle": "Pregunta en qué distrito está la persona."})
        franjas = [f.model_dump() if isinstance(f, BaseModel) else f for f in franjas]
        capturado = _grupo(grupo)  # lo que la persona dijo de su turno: se guarda para la sesión
        solicitud = {
            "estudiante_id": sesion.estudiante_id,
            "motivo": motivo,
            "distrito": distrito,
            "grupo": capturado or sesion.contexto.grupo or _grupo_por_horas(franjas),
            "franjas": franjas,
            "canales_aceptables": canales_aceptables,
        }
        resultado = puerto.proponer(solicitud, k)
        sesion.lote_disponible = False
        if resultado.get("motivo_vacio") == "servicios_en_lote":
            # Los servicios compatibles están en modo lote: no hay opciones para elegir; se ofrece el lote.
            sesion.ultima_solicitud = solicitud
            sesion.propuestas = {}
            sesion.desencuentro_registrado = False
            sesion.lote_disponible = True
            registrar("proponer_opciones", True, resultado)
            lote = resultado["lote"]
            return _json(
                {
                    "opciones": [],
                    "motivo_vacio": "servicios_en_lote",
                    "lote": {
                        "servicios": lote["servicios"],
                        "umbral_pct": lote["umbral_pct"],
                        "cierra_solo_en_segundos": lote["ventana_s"],
                        "solicitudes_esperando": lote["pendientes"],
                    },
                    "indicacion": (
                        "Todo lo compatible está en servicios con ocupación alta, que se reparten por lote: un grupo "
                        "de solicitudes se asigna en conjunto y el lote se cierra solo en unos segundos. Explícaselo en "
                        "simple, aclara que el horario lo decide el lote y pregúntale si quiere entrar. Si acepta, usa "
                        "`entrar_a_lote`."
                    ),
                }
            )
        if resultado.get("motivo_vacio") == "solicitud_invalida":
            registrar("proponer_opciones", False, resultado)
            return _json({"ok": False, "error": "solicitud_invalida", "detalle": resultado.get("detalle", "")})
        if capturado:
            sesion.contexto.grupo = capturado
        sesion.contexto.distrito = distrito  # si cambió de distrito, queda para el resto de la conversación
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

    def entrar_a_lote() -> str:
        if not sesion.lote_disponible or sesion.ultima_solicitud is None:
            resultado = {
                "ok": False,
                "error": "sin_oferta_de_lote",
                "detalle": "Solo se entra al lote cuando proponer_opciones dijo que todo está en servicios_en_lote.",
            }
            registrar("entrar_a_lote", False, resultado)
            return _json(resultado)
        ultima = next(
            (m.content for m in reversed(sesion.mensajes)
             if m.type == "ai" and isinstance(m.content, str) and m.content and not getattr(m, "tool_calls", None)),
            "",
        )
        if not entrada.acepta_lote(ctx.mensaje, ultima):
            resultado = {
                "ok": False,
                "error": "falta_confirmacion",
                "detalle": "La persona no aceptó entrar al lote. Pregúntale si quiere entrar y espera su respuesta.",
            }
            registrar("entrar_a_lote", False, resultado)
            return _json(resultado)
        resultado = puerto.entrar_a_lote(sesion.ultima_solicitud, sesion.estudiante_id, sesion.id)
        registrar("entrar_a_lote", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            return _json({"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")})
        sesion.lote_disponible = False
        sesion.lote_id = resultado["lote"]["id"]
        lote = resultado["lote"]
        return _json(
            {
                "ok": True,
                "lote": {"numero": lote["id"], "tu_posicion": lote["posicion"], "se_cierra_en": lote["cierra_en"]},
                "indicacion": (
                    "Quedó en el lote. Dile que el lote se cierra solo en unos segundos (o antes si se llena), que se "
                    "asigna en conjunto y que le avisarás aquí con su cita; no prometas día ni hora."
                ),
            }
        )

    def consultar_asistencia() -> str:
        textos = [m.content for m in sesion.mensajes if m.type == "human" and isinstance(m.content, str)]
        if not any(entrada.menciona_asistencia(t) for t in textos + [ctx.mensaje]):
            resultado = {
                "ok": False,
                "error": "no_pidio_asistencia",
                "detalle": "La persona no habló de su asistencia a clases. No consultes ese dato por tu cuenta.",
            }
            registrar("consultar_asistencia", False, resultado)
            return _json(resultado)
        resultado = puerto.asistencia(sesion.estudiante_id)
        registrar("consultar_asistencia", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            return _json({"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")})
        return _json(
            {
                "periodo": resultado["periodo"],
                "asistencia_actual": _pct(resultado["asistencia_actual"]),
                "asistencia_periodo_anterior": _pct(resultado["asistencia_periodo_anterior"]),
                "cambio_puntos": round(100 * resultado["variacion"]),
                "minimo_requerido": _pct(resultado["minimo_requerido"]),
                "cursos": [
                    {
                        "curso": c["curso"],
                        "asistencia": _pct(c["tasa"]),
                        "faltas": c["faltas"],
                        "de_sesiones": c["sesiones"],
                        "bajo_el_minimo": c["bajo_minimo"],
                    }
                    for c in resultado["cursos"]
                ],
                "indicacion": (
                    "Cuéntale sus cifras en simple (las de este período, cómo van frente al período anterior y qué "
                    "cursos están bajo el mínimo). No interpretes ni diagnostiques, no hables de riesgo ni de avisos, y "
                    "no tienes acceso a sus notas. Si le preocupa o le pesa, ofrécele buscarle una cita de bienestar."
                ),
            }
        )

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
            func=entrar_a_lote,
            name="entrar_a_lote",
            description=(
                "Pone a la persona en el lote de asignación conjunta. Úsala SOLO después de que proponer_opciones "
                "devolvió servicios_en_lote y la persona aceptó entrar."
            ),
            args_schema=SinArgs,
        ),
        StructuredTool.from_function(
            func=consultar_asistencia,
            name="consultar_asistencia",
            description=(
                "Consulta la asistencia a clases de la persona (este período, el anterior y por curso). Solo lectura y "
                "solo asistencia: no hay notas. Úsala únicamente si la persona habló de su asistencia o de sus faltas."
            ),
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
