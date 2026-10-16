"""El agente: un modelo de Ollama (por defecto qwen3.5:4b) con las herramientas de la agenda."""

import logging
import re
from dataclasses import dataclass, field
from datetime import date

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from . import guardrails
from .config import ConfigAgente
from .crisis import detectar_crisis, mensaje_crisis
from .entrada import detectar_inyeccion
from .errores import AgenteNoDisponible
from .herramientas import ContextoTurno, EventoHerramienta, construir_herramientas
from .prompt import construir_prompt
from .puerto import PuertoAgenda
from .sesion import SesionChat

logger = logging.getLogger(__name__)

# Acciones que cambian algo en la plataforma: si ya ocurrieron en un intento que falló, no se reintenta el turno.
_ACCIONES = {"reservar_cita", "cancelar_cita", "registrar_desencuentro", "avisarme_si_hay_cupo"}
# Un modelo pequeño a veces «escribe» la llamada a la herramienta como texto en vez de emitirla.
_LLAMADA_EN_TEXTO = re.compile(r'^\s*(<tool_call>|```|\{\s*"(name|tool|function|arguments|parameters)")', re.IGNORECASE)

SIN_RESPUESTA = (
    "No logré terminar eso. ¿Me lo cuentas de nuevo con otras palabras? Por ejemplo: qué días y a qué horas "
    "puedes asistir y si prefieres videollamada, teléfono o presencial."
)


@dataclass
class ResultadoTurno:
    respuesta: str
    eventos: list[EventoHerramienta] = field(default_factory=list)
    crisis: bool = False
    guardrail: str | None = None  # `limite_clinico` | `datos_profesionales`: respondió la capa determinística, sin modelo


def crear_modelo(config: ConfigAgente):
    """Cliente de Ollama para LangChain. Falla con un mensaje claro si falta la dependencia."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as error:  # pragma: no cover
        raise AgenteNoDisponible(
            "Falta langchain-ollama. Instala las dependencias del agente: uv sync --extra agente"
        ) from error
    return ChatOllama(
        model=config.modelo,
        base_url=config.url,
        temperature=config.temperatura,
        num_ctx=config.num_ctx,
        reasoning=config.razonamiento,
        keep_alive=config.keep_alive,
        client_kwargs={"timeout": config.timeout_s},
    )


def _texto(contenido) -> str:
    """El contenido de un AIMessage puede ser texto o una lista de bloques."""
    if isinstance(contenido, str):
        return contenido.strip()
    partes = [b if isinstance(b, str) else b.get("text", "") for b in contenido or [] if b]
    return "".join(partes).strip()


def _recortar(mensajes: list, max_turnos: int) -> list:
    """Conserva los últimos `max_turnos` mensajes de la persona (y todo lo que sigue a cada uno)."""
    inicios = [i for i, m in enumerate(mensajes) if isinstance(m, HumanMessage)]
    if len(inicios) <= max_turnos:
        return list(mensajes)
    return list(mensajes[inicios[-max_turnos] :])


def _respaldo(eventos: list[EventoHerramienta]) -> str:
    """Texto mínimo cuando el modelo hizo la acción pero no redactó respuesta."""
    for e in reversed(eventos):
        if e.nombre == "reservar_cita" and not e.ok and e.resultado.get("error") == "ya_tiene_cita":
            return e.resultado["mensaje"]
        if e.nombre == "reservar_cita" and e.ok and e.resultado.get("estado") == "pendiente":
            return e.resultado["mensaje"]
        if e.nombre == "reservar_cita" and e.ok:
            c = e.resultado["cita"]
            return (
                f"Listo, tu cita quedó confirmada: {c['servicio_nombre']}, el {c['fecha']} de "
                f"{c['hora_inicio']} a {c['hora_fin']}. Tu número de cita es {c['id']}. {c.get('aviso_canal', '')}"
            ).strip()
        if e.nombre == "cancelar_cita" and e.ok:
            return f"Listo, cancelé la cita {e.resultado['cita']['id']}."
        if e.nombre == "registrar_desencuentro" and e.ok:
            return "Avisé al equipo de coordinación que no había una opción para ti, para que amplíen la oferta."
        if e.nombre == "proponer_opciones" and e.ok:
            if e.resultado.get("opciones"):
                aviso = e.resultado.get("mensaje")
                cuerpo = "Estas son las opciones que encontré. Toca la que prefieras o escríbeme cuál."
                return f"{aviso} {cuerpo}" if aviso else cuerpo
            if e.resultado.get("motivo_vacio") == "sin_cupos_compatibles":
                return e.resultado.get("mensaje") or "No encontré cupos dentro de los días y horarios que puedes."
    return SIN_RESPUESTA


class AgenteAura:
    """Conversa con una persona y llama a las herramientas. No guarda estado: la sesión lo trae."""

    def __init__(self, config: ConfigAgente | None = None, modelo=None):
        self.config = config or ConfigAgente.desde_entorno()
        self._modelo = modelo  # inyectable en pruebas; si no, se crea al primer uso

    @property
    def modelo(self):
        if self._modelo is None:
            self._modelo = crear_modelo(self.config)
        return self._modelo

    def responder(self, sesion: SesionChat, mensaje: str, puerto: PuertoAgenda, hoy: date) -> ResultadoTurno:
        if detectar_crisis(mensaje):
            texto = mensaje_crisis(self.config.linea_ayuda)
            sesion.mensajes += [HumanMessage(mensaje), AIMessage(texto)]
            sesion.tocar()
            return ResultadoTurno(texto, crisis=True)

        if detectar_inyeccion(mensaje):
            texto = (
                "Soy AURA, la asistente de citas de bienestar estudiantil. No puedo cambiar de rol, "
                "ignorar mis directivas de seguridad ni realizar tareas fuera de mi funci?n. "
                "?En qu? puedo ayudarte respecto a tus citas de apoyo?"
            )
            sesion.mensajes += [HumanMessage(mensaje), AIMessage(texto)]
            sesion.tocar()
            return ResultadoTurno(texto)

        limite = guardrails.evaluar(mensaje)  # capa determin?stica: ni medicamentos, ni diagn?sticos, ni contactos
        if limite:
            sesion.mensajes += [HumanMessage(mensaje), AIMessage(limite.texto)]
            sesion.tocar()
            return ResultadoTurno(limite.texto, guardrail=limite.tipo)

        entrada = _recortar(sesion.mensajes, self.config.max_turnos - 1) + [HumanMessage(mensaje)]
        for intento in (1, 2):
            ctx = ContextoTurno(sesion, puerto, mensaje)
            agente = create_agent(
                self.modelo, construir_herramientas(ctx), system_prompt=construir_prompt(hoy, sesion)
            )
            try:
                salida = agente.invoke(
                    {"messages": entrada}, config={"recursion_limit": 2 * self.config.max_pasos + 1}
                )
            except Exception as error:  # noqa: BLE001 — se clasifica abajo
                if type(error).__name__ == "GraphRecursionError":
                    return self._cerrar_con_respaldo(sesion, entrada, ctx)  # si ya hizo algo útil, se dice; si no, pide reformular
                clasificado = _clasificar(error, self.config)
                if clasificado is not error:  # Ollama apagado o sin el modelo: no es una llamada mal formada
                    raise clasificado from error
                # Llamada a herramienta mal formada (u otro fallo del modelo): se reintenta una vez; si vuelve a fallar,
                # se responde con un mensaje seguro. El chat no se rompe.
                logger.warning("Fallo del agente (intento %s): %s", intento, error, exc_info=error)
                if intento == 1 and not _hubo_acciones(ctx.eventos):
                    continue
                return self._cerrar_con_respaldo(sesion, entrada, ctx)

            ultimo = salida["messages"][-1] if salida["messages"] else None
            respuesta = _texto(ultimo.content) if isinstance(ultimo, AIMessage) and not ultimo.tool_calls else ""
            if respuesta and _LLAMADA_EN_TEXTO.search(respuesta):  # escribió la llamada como texto en vez de hacerla
                logger.warning("El modelo escribió una llamada a herramienta como texto (intento %s)", intento)
                if intento == 1 and not _hubo_acciones(ctx.eventos):
                    continue
                return self._cerrar_con_respaldo(sesion, entrada, ctx)
            sesion.mensajes = list(salida["messages"])
            sesion.tocar()
            return ResultadoTurno(respuesta or _respaldo(ctx.eventos), ctx.eventos)
        raise AssertionError("inalcanzable")  # pragma: no cover

    @staticmethod
    def _cerrar_con_respaldo(sesion: SesionChat, entrada: list, ctx: ContextoTurno) -> ResultadoTurno:
        texto = _respaldo(ctx.eventos)
        sesion.mensajes = entrada + [AIMessage(texto)]
        sesion.tocar()
        return ResultadoTurno(texto, ctx.eventos)


def _hubo_acciones(eventos: list[EventoHerramienta]) -> bool:
    """¿Ya cambió algo en la plataforma en este turno? Entonces no se reintenta (no se duplica una reserva)."""
    return any(e.ok and e.nombre in _ACCIONES for e in eventos)


def _clasificar(error: Exception, config: ConfigAgente) -> Exception:
    """Convierte fallos de conexión con Ollama en `AgenteNoDisponible`; el resto se deja pasar."""
    nombre = type(error).__name__
    texto = str(error).lower()
    if nombre in {"ConnectError", "ConnectTimeout", "ReadTimeout", "TimeoutException"} or isinstance(
        error, (ConnectionError, TimeoutError)
    ):
        return AgenteNoDisponible(
            f"No se pudo conectar con Ollama en {config.url}. Abre Ollama (`ollama serve`) y revisa AURA_OLLAMA_URL."
        )
    if nombre == "ResponseError" and ("not found" in texto or "pull" in texto):
        return AgenteNoDisponible(
            f"Ollama no tiene el modelo «{config.modelo}». Descárgalo con `ollama pull {config.modelo}` "
            "o cambia AURA_OLLAMA_MODEL por el nombre que ves en `ollama list`."
        )
    if nombre == "ResponseError" and "tool" in texto:
        return AgenteNoDisponible(
            f"El modelo «{config.modelo}» no admite herramientas (tool calling) en tu versión de Ollama. "
            "Actualiza Ollama o usa otro modelo con soporte de herramientas."
        )
    return error
