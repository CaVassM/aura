"""El agente: un modelo de Ollama (por defecto gemma4) con las herramientas de la agenda."""

from dataclasses import dataclass, field
from datetime import date

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from .config import ConfigAgente
from .crisis import detectar_crisis, mensaje_crisis
from .errores import AgenteNoDisponible
from .herramientas import ContextoTurno, EventoHerramienta, construir_herramientas
from .prompt import construir_prompt
from .puerto import PuertoAgenda
from .sesion import SesionChat

SIN_RESPUESTA = (
    "No logré terminar eso. ¿Me lo cuentas de nuevo con otras palabras? Por ejemplo: qué días y a qué horas "
    "puedes asistir y si prefieres videollamada, teléfono o presencial."
)


@dataclass
class ResultadoTurno:
    respuesta: str
    eventos: list[EventoHerramienta] = field(default_factory=list)
    crisis: bool = False


def crear_modelo(config: ConfigAgente):
    """Cliente de Ollama para LangChain. Falla con un mensaje claro si falta la dependencia."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as error:  # pragma: no cover
        raise AgenteNoDisponible(
            "Falta langchain-ollama. Instala las dependencias del agente: pip install -r requirements-agente.txt"
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
        if e.nombre == "reservar_cita" and e.ok:
            c = e.resultado["cita"]
            return (
                f"Listo, tu cita quedó confirmada: {c['servicio_nombre']}, el {c['fecha']} de "
                f"{c['hora_inicio']} a {c['hora_fin']}. Tu número de cita es {c['id']}."
            )
        if e.nombre == "cancelar_cita" and e.ok:
            return f"Listo, cancelé la cita {e.resultado['cita']['id']}."
        if e.nombre == "registrar_desencuentro" and e.ok:
            return "Avisé al equipo de coordinación que no había una opción para ti, para que amplíen la oferta."
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

        ctx = ContextoTurno(sesion, puerto, mensaje)
        agente = create_agent(
            self.modelo, construir_herramientas(ctx), system_prompt=construir_prompt(hoy, sesion)
        )
        entrada = _recortar(sesion.mensajes, self.config.max_turnos - 1) + [HumanMessage(mensaje)]
        try:
            salida = agente.invoke(
                {"messages": entrada}, config={"recursion_limit": 2 * self.config.max_pasos + 1}
            )
        except Exception as error:  # noqa: BLE001 — se clasifica abajo
            if type(error).__name__ == "GraphRecursionError":
                sesion.mensajes = entrada + [AIMessage(SIN_RESPUESTA)]
                sesion.tocar()
                return ResultadoTurno(SIN_RESPUESTA, ctx.eventos)
            raise _clasificar(error, self.config) from error

        sesion.mensajes = list(salida["messages"])
        sesion.tocar()
        ultimo = sesion.mensajes[-1] if sesion.mensajes else None
        respuesta = _texto(ultimo.content) if isinstance(ultimo, AIMessage) and not ultimo.tool_calls else ""
        return ResultadoTurno(respuesta or _respaldo(ctx.eventos), ctx.eventos)


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
