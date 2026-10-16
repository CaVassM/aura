"""Chat con el agente: lleva la sesión y conecta al agente con las citas de la plataforma.

El agente no toca el motor directamente: reserva y cancela a través de `CitasService`, de modo
que una cita hecha por chat aparece en «Mis citas» y en Coordinación igual que una hecha por la API.
"""

from dataclasses import asdict, fields
from datetime import date

from typing import TYPE_CHECKING

import httpx
from agente.config import ConfigAgente
from agente.errores import AgenteNoDisponible
from agente.sesion import ContextoEstudiante, SesionChat

from ..models import Cita
from ..repositories.app_state import AppState
from ..schemas.citas import cita_out
from .academico_service import AcademicoService
from .citas_service import CitasService
from .errors import (
    AgenteNoDisponibleError,
    InvalidRequestError,
    NotFoundError,
    PlatformError,
    SlotTakenError,
    YaEnLoteError,
    YaTieneCitaError,
)
from .etiquetas import Etiquetas
from .lista_espera_service import ListaEsperaService

if TYPE_CHECKING:  # el agente importa LangChain: se carga solo al usar el chat (ver deps.get_agente)
    from agente.agente import AgenteAura

_CAMPOS_CITA = {f.name for f in fields(Cita)}


class PuertoPlataforma:
    """Implementa `agente.puerto.PuertoAgenda` sobre los servicios de la plataforma."""

    def __init__(self, estado: AppState):
        self._estado = estado
        self._citas = CitasService(estado)
        self._etiquetas = Etiquetas(estado.tablas)

    def _cita(self, cita: Cita) -> dict:
        datos = asdict(cita)
        datos["canal_label"] = self._etiquetas.canal(cita.canal)
        datos["aviso_canal"] = self._etiquetas.confirmacion_canal(cita.canal, cita.servicio_nombre, cita.distrito)
        datos["dia_semana"] = self._etiquetas.dia_largo(date.fromisoformat(cita.fecha).weekday())
        return datos

    @staticmethod
    def _error(error: PlatformError) -> dict:
        return {"ok": False, "error": error.code, "detalle": error.detalle}

    def proponer(self, solicitud: dict, k: int) -> dict:
        try:
            return self._citas.proponer(solicitud, k)
        except InvalidRequestError as error:
            return {"opciones": [], "motivo_vacio": "solicitud_invalida", "detalle": error.detalle}

    def reservar(
        self,
        estudiante_id: str,
        opcion_id: str,
        servicio_ideal: str | None,
        solicitud: dict | None = None,
        sesion_id: str | None = None,
        reemplazar: bool = False,
    ) -> dict:
        try:
            resultado = self._citas.reservar_opcion(
                estudiante_id, opcion_id, servicio_ideal, origen="chat", solicitud=solicitud, sesion_id=sesion_id, reemplazar=reemplazar
            )
        except YaTieneCitaError as error:
            return {"ok": False, "error": error.code, "detalle": error.detalle, "cita": error.cita, "mensaje": error.mensaje}
        except (SlotTakenError, InvalidRequestError, YaEnLoteError) as error:
            return self._error(error)
        if resultado["estado"] == "pendiente":
            return {"ok": True, **resultado}
        return {"ok": True, "estado": "confirmada", "cita": self._cita(resultado["cita"])}

    def cancelar(self, cita_id: str, estudiante_id: str) -> dict:
        try:
            return {"ok": True, "cita": self._cita(self._citas.cancelar(cita_id, estudiante_id, origen="chat"))}
        except NotFoundError as error:
            return {"ok": False, "error": "cita_no_encontrada", "detalle": error.detalle}

    def listar_citas(self, estudiante_id: str) -> list[dict]:
        return [self._cita(c) for c in self._citas.listar(estudiante_id)]

    def anotar_lista_espera(self, solicitud: dict, estudiante_id: str, sesion_id: str) -> dict:
        try:
            entrada = ListaEsperaService(self._estado).anotar(estudiante_id, solicitud, sesion_id, origen="chat")
        except PlatformError as error:
            return self._error(error)
        return {"ok": True, "espera": {"id": entrada["id"], "servicio_ideal_label": entrada["servicio_ideal_label"], "franjas": entrada["franjas"]}}

    def asistencia(self, estudiante_id: str) -> dict:
        return AcademicoService(self._estado).asistencia_para_agente(estudiante_id)

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        # Solo es un desencuentro si no existe ningún cupo compatible (ni normal ni en lote): se verifica antes de registrar
        return self._citas.registrar_desencuentro(solicitud, origen="chat", verificar=True)


class ChatService:
    def __init__(self, estado: AppState, agente: "AgenteAura | None"):
        self._estado = estado
        self._agente = agente
        self._puerto = PuertoPlataforma(estado)

    # --- sesiones ---

    def _sesion(self, session_id: str | None, estudiante_id: str) -> SesionChat:
        repo = self._estado.chats
        if session_id is None:
            return repo.crear(estudiante_id, ContextoEstudiante())
        sesion = repo.obtener(session_id)
        if sesion is None or sesion.estudiante_id != estudiante_id:
            raise NotFoundError(session_id)
        return sesion

    def _distrito_valido(self, distrito: str | None) -> str | None:
        if distrito is None:
            return None
        distritos = {s["distrito"] for s in self._estado.motor.servicios()}
        if distrito.upper() not in distritos:
            raise InvalidRequestError(f"Distrito desconocido: {distrito}. Válidos: {', '.join(sorted(distritos))}")
        return distrito.upper()

    # --- casos de uso ---

    def conversar(
        self,
        mensaje: str,
        estudiante_id: str,
        session_id: str | None = None,
        distrito: str | None = None,
        grupo: str | None = None,
    ) -> dict:
        distrito = self._distrito_valido(distrito)
        sesion = self._sesion(session_id, estudiante_id)
        with self._estado.chats.candado(sesion.id):
            if distrito:
                sesion.contexto.distrito = distrito
            if grupo:
                sesion.contexto.grupo = grupo
            try:
                resultado = self._agente.responder(sesion, mensaje, self._puerto, self._estado.hoy)
            except AgenteNoDisponible as error:
                raise AgenteNoDisponibleError(str(error)) from error
        return self._respuesta(sesion.id, resultado)

    def _respuesta(self, session_id: str, resultado) -> dict:
        opciones, cita, cancelada, desencuentro = [], None, None, False
        lote, lista_espera, mensaje, ya_tiene = None, None, None, None
        for evento in resultado.eventos:
            if evento.nombre == "reservar_cita" and evento.resultado.get("error") == "ya_tiene_cita":
                ya_tiene = {"cita": evento.resultado["cita"], "mensaje": evento.resultado["mensaje"]}
            if not evento.ok:
                continue
            if evento.nombre == "proponer_opciones":
                opciones, mensaje = evento.resultado["opciones"], evento.resultado.get("mensaje")
            elif evento.nombre == "reservar_cita":
                opciones, ya_tiene = [], None
                if evento.resultado.get("estado") == "pendiente":  # eligió un servicio en lote: queda esperando
                    lote = evento.resultado["lote"]
                else:
                    cita = self._cita_out(evento.resultado["cita"])
            elif evento.nombre == "cancelar_cita":
                cancelada = self._cita_out(evento.resultado["cita"])
            elif evento.nombre == "registrar_desencuentro":
                desencuentro = True
            elif evento.nombre == "avisarme_si_hay_cupo":
                lista_espera = evento.resultado["espera"]
        return {
            "session_id": session_id,
            "respuesta": resultado.respuesta,
            "opciones": opciones,
            "cita": cita,
            "cita_cancelada": cancelada,
            "desencuentro_registrado": desencuentro,
            "lote": lote,
            "mensaje": mensaje,
            "ya_tiene_cita": ya_tiene,
            "lista_espera": lista_espera,
            "alerta_crisis": resultado.crisis,
            "herramientas_usadas": [{"nombre": e.nombre, "ok": e.ok} for e in resultado.eventos],
        }

    @staticmethod
    def _cita_out(datos: dict):
        return cita_out(Cita(**{k: v for k, v in datos.items() if k in _CAMPOS_CITA}))

    def historial(self, session_id: str, estudiante_id: str) -> dict:
        sesion = self._sesion(session_id, estudiante_id)
        mensajes = []
        for m in sesion.mensajes:
            texto = m.content if isinstance(m.content, str) else ""
            if m.type == "human" and texto:
                mensajes.append({"rol": "user", "texto": texto})
            elif m.type == "ai" and texto and not getattr(m, "tool_calls", None):
                mensajes.append({"rol": "agent", "texto": texto})
        return {"session_id": sesion.id, "mensajes": mensajes}

    def reiniciar(self, session_id: str, estudiante_id: str) -> dict:
        sesion = self._sesion(session_id, estudiante_id)
        self._estado.chats.eliminar(sesion.id)
        return {"ok": True}


def estado_ollama(config: ConfigAgente, dependencias: bool = True) -> dict:
    """Diagnóstico para el portal y para quien configura el equipo: ¿responde Ollama y está el modelo?"""
    base = {"modelo": config.modelo, "url": config.url, "dependencias_instaladas": dependencias}
    try:
        etiquetas = httpx.get(f"{config.url}/api/tags", timeout=3).json().get("models", [])
    except (httpx.HTTPError, ValueError):
        return {
            **base,
            "ollama_disponible": False,
            "modelo_instalado": False,
            "detalle": f"No responde Ollama en {config.url}. Ábrelo o ejecuta `ollama serve`.",
        }
    nombres = {m.get("name", "") for m in etiquetas} | {m.get("name", "").split(":")[0] for m in etiquetas}
    instalado = config.modelo in nombres
    detalle = "Listo." if instalado else f"Falta el modelo: ejecuta `ollama pull {config.modelo}`."
    if not dependencias:
        detalle = "Faltan dependencias: uv sync --extra agente"
    return {**base, "ollama_disponible": True, "modelo_instalado": instalado, "detalle": detalle}
