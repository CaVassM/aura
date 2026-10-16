"""Herramientas LangChain del agente, creadas para cada mensaje.

Diferencias deliberadas con las herramientas del motor (`aura.herramientas`):
- El modelo NO elige el `estudiante_id`: sale de la sesión, así nadie reserva ni cancela a nombre de otra persona.
- `reservar_cita` recibe el NÚMERO de la opción elegida (1, 2, 3…) de la última lista; el modelo nunca ve ni copia
  identificadores internos, así que no puede inventarlos ni mostrárselos a la persona. Una opción puede ser un cupo
  (queda la cita) o un servicio en modo lote (queda pendiente y el resultado llega después al mismo chat).
- `proponer_opciones` se niega a buscar si la persona no ha dicho días ni canal, y `cancelar_cita` se niega si la
  persona no pidió cancelar ni confirmó una pregunta de cancelar (ver `entrada.py`). Reemplazar una cita (R7) también
  exige que la persona lo confirme.
- `registrar_desencuentro` no recibe argumentos: usa la última solicitud buscada, y la plataforma solo lo registra si no
  existe ningún cupo compatible.
- Las reglas viven en la plataforma: las respuestas traen el texto (`mensaje`) que el modelo muestra tal cual.
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
    busquedas: set = field(default_factory=set)  # búsquedas ya hechas en este turno (frena los bucles)


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
    fecha: str = Field(
        default="",
        description=(
            "AAAA-MM-DD. Solo si la persona pidió una FECHA concreta (p. ej. «el 18 de noviembre»). Si dijo solo el día de la "
            "semana («el miércoles»), déjalo vacío. Con fecha, solo se buscan cupos de ese día"
        ),
    )
    service_id_preferido: str = Field(
        default="",
        description=(
            "Solo si la persona nombró un servicio concreto («quiero Brújula», «Espacio Lumen Pares»): su nombre tal como lo "
            "dijo. Sus opciones salen primero. Si no nombró ninguno, déjalo vacío"
        ),
    )
    k: int = Field(default=3, ge=1, le=5, description="Cuántas opciones buscar (se muestran 3 como máximo)")


class ReservarArgs(BaseModel):
    numero: int = Field(ge=1, description="Número de la opción que la persona eligió en la última lista (1, 2, 3…)")
    reemplazar: bool = Field(
        default=False,
        description=(
            "true SOLO si la herramienta avisó que ya tiene una cita de ese tipo y la persona confirmó cambiarla por la nueva"
        ),
    )


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


def _firma_desencuentro(solicitud: dict, servicio_ideal: str | None) -> str:
    """Un desencuentro es de una persona (la sesión), un servicio ideal y una franja: lo mismo no se registra dos veces."""
    franjas = sorted((f["dia"], f["desde"], f["hasta"]) for f in solicitud["franjas"])
    return json.dumps([servicio_ideal, franjas])


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
    tipo = o.get("tipo_label", o["tipo"])
    if o.get("tipo_opcion") == "lote":
        texto = f"{o['servicio_nombre']} ({tipo}) · asignación en grupo (lote): el día y la hora los decide el lote. {o['mensaje']}"
        if o["es_alternativa"]:
            texto += " Es un servicio distinto al ideal, pero compatible."
        return {"numero": numero, "texto": texto, "distrito": o["distrito"], "es_lote": True}
    canal = o.get("canal_label", o["canal"])
    texto = f"{o['servicio_nombre']} ({tipo}) · {_fecha_texto(o['fecha'])}, de {o['hora_inicio']} a {o['hora_fin']} · {canal}"
    if o["es_alternativa"]:
        texto += " · servicio distinto al ideal, pero compatible"
    return {"numero": numero, "texto": texto, "distrito": o["distrito"], "dias_de_espera": o["dias_espera"]}


def _cita_para_modelo(c: dict) -> dict:
    canal = c.get("canal_label", c["canal"])
    datos = {
        "cita_id": c["id"],
        "texto": f"{c['servicio_nombre']} ({c.get('tipo_label', c['tipo'])}) · {_fecha_texto(c['fecha'])}, "
        f"de {c['hora_inicio']} a {c['hora_fin']} · {canal}",
        "estado": c["estado"],
    }
    if c.get("aviso_canal"):
        datos["aviso_canal"] = c["aviso_canal"]
    return datos


def _ultima_respuesta(sesion: SesionChat) -> str:
    """Lo último que el agente le dijo a la persona (sin contar llamadas a herramientas)."""
    return next(
        (m.content for m in reversed(sesion.mensajes)
         if m.type == "ai" and isinstance(m.content, str) and m.content and not getattr(m, "tool_calls", None)),
        "",
    )


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
        fecha: str = "",
        service_id_preferido: str = "",
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
        fecha = fecha.strip()
        if fecha:
            try:
                dia_fecha = date.fromisoformat(fecha)
            except ValueError:
                resultado = {"ok": False, "error": "fecha_invalida", "detalle": "`fecha` debe ser AAAA-MM-DD, p. ej. 2026-11-18."}
                registrar("proponer_opciones", False, resultado)
                return _json(resultado)
            # La fecha manda sobre el día de la semana que pusiera el modelo; las horas se respetan.
            nombre_dia = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[dia_fecha.weekday()]
            franjas = [{**f, "dia": nombre_dia} for f in franjas]
        preferido = service_id_preferido.strip()
        firma = _json([motivo, distrito, franjas, sorted(canales_aceptables), fecha, preferido, k])
        if firma in ctx.busquedas:
            resultado = {
                "ok": False,
                "error": "busqueda_repetida",
                "detalle": "Ya hiciste exactamente esta búsqueda en este mensaje. No la repitas: respóndele a la persona con lo que ya obtuviste.",
            }
            registrar("proponer_opciones", False, resultado)
            return _json(resultado)
        ctx.busquedas.add(firma)
        capturado = _grupo(grupo)  # lo que la persona dijo de su turno: se guarda para la sesión
        solicitud = {
            "estudiante_id": sesion.estudiante_id,
            "motivo": motivo,
            "distrito": distrito,
            "grupo": capturado or sesion.contexto.grupo or _grupo_por_horas(franjas),
            "franjas": franjas,
            "canales_aceptables": canales_aceptables,
        }
        if fecha:
            solicitud["fecha"] = fecha
        if preferido:
            solicitud["service_id_preferido"] = preferido
        resultado = puerto.proponer(solicitud, k)
        aviso_fecha = ""
        if fecha and not resultado.get("opciones"):
            # Nada ese día: se buscan las fechas más cercanas con las mismas preferencias y se dice claro.
            resultado = puerto.proponer({k_: v for k_, v in solicitud.items() if k_ != "fecha"}, k)
            if resultado.get("opciones"):
                aviso_fecha = (
                    f"No hay cupos el {_fecha_texto(fecha)} con esas preferencias. Estas son las fechas más cercanas "
                    "que encontré (no son de ese día)."
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
        sesion.reemplazo_pendiente = None
        sesion.propuestas = {o["opcion_id"]: o for o in resultado["opciones"]}
        if aviso_fecha:
            resultado = {**resultado, "mensaje": " ".join(t for t in (aviso_fecha, resultado.get("mensaje")) if t)}
        registrar("proponer_opciones", True, resultado)
        if not resultado["opciones"]:
            # Sin ningún cupo compatible (ni normal ni en lote) ES un desencuentro. Lo registra la herramienta, no el modelo:
            # un modelo pequeño se salta ese paso y la regla no puede depender de que lo recuerde.
            firma = _firma_desencuentro(solicitud, sesion.servicio_ideal)
            if firma in sesion.desencuentros_firmas:  # ya quedó registrado en esta conversación: no se duplica
                registro = {"ok": True, "detalle": "Ya estaba registrado para esta franja."}
            else:
                registro = puerto.registrar_desencuentro(solicitud)
                if registro.get("ok"):
                    sesion.desencuentros_firmas.add(firma)
                    registrar("registrar_desencuentro", True, registro)
            sesion.desencuentro_registrado = bool(registro.get("ok"))
            return _json(
                {
                    "opciones": [],
                    "motivo_vacio": resultado.get("motivo_vacio", "sin_cupos_compatibles"),
                    "mensaje": resultado.get("mensaje"),
                    "desencuentro_registrado": bool(registro.get("ok")),
                    "indicacion": (
                        "No hubo cupos dentro de lo que la persona puede y el equipo de coordinación ya quedó avisado. Muéstrale el "
                        "`mensaje` tal cual y pregúntale si quiere que le avises aquí si se libera un cupo; solo si dice que sí, usa "
                        "`avisarme_si_hay_cupo`. No le propongas otros días, horas ni canales."
                    ),
                }
            )
        indicacion = (
            "Muestra cada opción con su `texto`, numeradas, y pregunta cuál prefiere. Di siempre la fecha completa de cada una. "
            "Si hay `mensaje`, muéstralo tal cual antes de las opciones; no lo reinterpretes ni digas que no hay cupos."
        )
        if any(o.get("tipo_opcion") == "lote" for o in resultado["opciones"]):
            indicacion += " Una opción por lote queda pendiente: la persona recibe su cita aquí mismo en unos segundos."
        datos = {
            "opciones": [_opcion_para_modelo(i, o) for i, o in enumerate(resultado["opciones"], 1)],
            "mensaje": resultado.get("mensaje"),
            "indicacion": indicacion,
        }
        return _json(datos)

    def reservar_cita(numero: int, reemplazar: bool = False) -> str:
        opciones = list(sesion.propuestas.values())
        pendiente = sesion.reemplazo_pendiente
        if reemplazar:
            if not pendiente or pendiente["opcion_id"] not in sesion.propuestas:
                resultado = {
                    "ok": False,
                    "error": "sin_cita_que_reemplazar",
                    "detalle": "Solo se reemplaza una cita después de que `reservar_cita` avisó que ya tiene una. Reserva sin `reemplazar`.",
                }
                registrar("reservar_cita", False, resultado)
                return _json(resultado)
            if not entrada.acepta_reemplazo(ctx.mensaje, _ultima_respuesta(sesion)):
                resultado = {
                    "ok": False,
                    "error": "falta_confirmacion",
                    "detalle": "La persona no confirmó cambiar su cita. Pregúntale si quiere cambiarla por la nueva y espera su respuesta.",
                }
                registrar("reservar_cita", False, resultado)
                return _json(resultado)
            opcion_id = pendiente["opcion_id"]  # lo que se confirma es la opción que chocó, no otra
        else:
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
        resultado = puerto.reservar(
            sesion.estudiante_id, opcion_id, sesion.servicio_ideal, sesion.ultima_solicitud, sesion.id, reemplazar
        )
        registrar("reservar_cita", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            if resultado.get("error") == "cupo_ya_tomado":
                sesion.propuestas.pop(opcion_id, None)
            if resultado.get("error") == "ya_tiene_cita":
                sesion.reemplazo_pendiente = {"opcion_id": opcion_id}  # a la espera de que la persona confirme el cambio
                return _json(
                    {
                        "ok": False,
                        "error": "ya_tiene_cita",
                        "mensaje": resultado["mensaje"],
                        "indicacion": (
                            "Muéstrale el `mensaje` tal cual y espera su respuesta. Si confirma el cambio, vuelve a llamar a "
                            "`reservar_cita` con el mismo número y reemplazar=true. Si no, deja la cita que ya tiene."
                        ),
                    }
                )
            return _json(
                {"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")}
            )
        sesion.propuestas = {}
        sesion.reemplazo_pendiente = None
        if resultado.get("estado") == "pendiente":
            lote = resultado["lote"]
            sesion.lote_id = lote["id"]
            return _json(
                {
                    "ok": True,
                    "estado": "pendiente",
                    "lote": {"numero": lote["id"], "tu_posicion": lote["posicion"], "se_cierra_en": lote["cierra_en"]},
                    "mensaje": resultado["mensaje"],
                    "indicacion": (
                        "Quedó pendiente en el lote. Muéstrale el `mensaje` tal cual; no prometas día ni hora: el resultado "
                        "(su cita u otras opciones) le llegará aquí mismo."
                    ),
                }
            )
        return _json(
            {
                "ok": True,
                "cita": _cita_para_modelo(resultado["cita"]),
                "indicacion": "Confirma con el `texto` de la cita y su `cita_id`, y agrega al final la línea `aviso_canal` tal cual.",
            }
        )

    def cancelar_cita(cita_id: str) -> str:
        if not entrada.confirma_cancelacion(ctx.mensaje, _ultima_respuesta(sesion)):
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

    def avisarme_si_hay_cupo() -> str:
        if sesion.ultima_solicitud is None or (sesion.propuestas and not sesion.desencuentro_registrado):
            resultado = {
                "ok": False,
                "error": "sin_busqueda_sin_cupo",
                "detalle": "Solo se anota a la persona cuando la última búsqueda no tuvo opciones.",
            }
            registrar("avisarme_si_hay_cupo", False, resultado)
            return _json(resultado)
        if not entrada.acepta_aviso(ctx.mensaje, _ultima_respuesta(sesion)):
            resultado = {
                "ok": False,
                "error": "falta_confirmacion",
                "detalle": "La persona no pidió que le avises. Pregúntale si quiere que le avises aquí si se libera un cupo y espera su respuesta.",
            }
            registrar("avisarme_si_hay_cupo", False, resultado)
            return _json(resultado)
        resultado = puerto.anotar_lista_espera(sesion.ultima_solicitud, sesion.estudiante_id, sesion.id)
        registrar("avisarme_si_hay_cupo", bool(resultado.get("ok")), resultado)
        if not resultado.get("ok"):
            return _json({"ok": False, "error": resultado.get("error", "error"), "detalle": resultado.get("detalle", "")})
        return _json(
            {
                "ok": True,
                "indicacion": (
                    "Quedó en la lista de espera. Dile que si se libera un cupo compatible le avisarás aquí mismo con la "
                    "opción lista para reservar; no prometas día ni hora, ni que lo conseguirá."
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
        firma = _firma_desencuentro(sesion.ultima_solicitud, sesion.servicio_ideal)
        if sesion.desencuentro_registrado or firma in sesion.desencuentros_firmas:
            sesion.desencuentro_registrado = True
            return _json({"ok": True, "detalle": "Ya estaba registrado para esta franja."})
        resultado = puerto.registrar_desencuentro(sesion.ultima_solicitud)
        registrar("registrar_desencuentro", bool(resultado.get("ok")), resultado)
        if resultado.get("ok"):
            sesion.desencuentro_registrado = True
            sesion.desencuentros_firmas.add(firma)
            resultado = {
                **resultado,
                "indicacion": (
                    "Díselo con honestidad y pregúntale si quiere que le avises aquí si se libera un cupo compatible. "
                    "Solo si dice que sí, usa `avisarme_si_hay_cupo`."
                ),
            }
        return _json(resultado)

    return [
        StructuredTool.from_function(
            func=proponer_opciones,
            name="proponer_opciones",
            description=(
                "Busca citas compatibles con lo que la persona necesita y devuelve hasta 3 opciones ordenadas "
                "de mejor a peor (un servicio con mucha demanda sale como opción de asignación en grupo). No reserva nada. Úsala en "
                "cuanto tengas motivo, días/horas y canal; si nombró un servicio, pásalo en `service_id_preferido`."
            ),
            args_schema=ProponerArgs,
        ),
        StructuredTool.from_function(
            func=reservar_cita,
            name="reservar_cita",
            description=(
                "Reserva la opción que la persona eligió de la última lista mostrada, por su número (si es una opción por "
                "lote, queda pendiente en el lote). Úsala SOLO tras una elección clara. Devuelve el comprobante de la cita, "
                "el estado pendiente del lote o un error."
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
            func=avisarme_si_hay_cupo,
            name="avisarme_si_hay_cupo",
            description=(
                "Anota a la persona en la lista de espera con su última búsqueda para avisarle aquí si se libera un cupo "
                "compatible. Úsala SOLO cuando no hubo opciones y la persona aceptó que le avises."
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
                "Avisa al equipo de coordinación que la última búsqueda no tuvo ninguna opción que sirviera. Normalmente ya "
                "queda registrado solo cuando `proponer_opciones` no devuelve opciones; si sí hubo cupos (normales o por lote), "
                "la plataforma la rechaza."
            ),
            args_schema=SinArgs,
        ),
    ]
