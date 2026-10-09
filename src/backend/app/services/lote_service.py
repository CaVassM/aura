"""Modo lote (docs/como_funciona.md §8).

Un servicio entra en modo lote cuando su utilización (cupos reservados / cupos liberados de la agenda abierta)
llega al umbral (`modo_lote_umbral_utilizacion`, 75 %). Sus cupos dejan de ofrecerse uno a uno: una solicitud que
solo encuentra servicios en lote espera en el **lote abierto**, que se cierra solo a los `lote.ventana_segundos`
de entrar la primera solicitud, o apenas junta `lote.tamano_maximo`. Al cerrarse, el algoritmo genético asigna
todas las solicitudes en conjunto (`aura.herramientas.lote`), la plataforma reserva las citas y avisa a cada
estudiante. Todo vive en RAM.
"""

import threading
from datetime import datetime, timedelta, timezone

from ..repositories.app_state import AppState
from ..repositories.lote_repository import Lote, SolicitudLote
from ..schemas.citas import cita_out
from .actividad_service import ActividadService
from .errors import InvalidRequestError, PlatformError, YaEnLoteError
from .etiquetas import Etiquetas
from .ocupacion import embudo_por_servicio, en_lote, porcentaje, umbral_lote


def _iso(momento: datetime) -> str:
    return momento.isoformat(timespec="milliseconds")


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class LoteService:
    def __init__(self, estado: AppState):
        self._e = estado
        self._cfg = estado.parametros["lote"]
        self._actividad = ActividadService(estado)
        self._etiquetas = Etiquetas(estado.tablas)

    # --- reglas ---

    def servicios_en_lote(self) -> set[str]:
        """Servicios con utilización ≥ umbral: sus cupos solo se reparten por lote."""
        _, _, por_servicio = embudo_por_servicio(self._e)
        return {sid for sid, f in por_servicio.items() if en_lote(self._e, f["reservados"], f["liberados"])}

    def info_oferta(self) -> dict:
        """Lo que necesita saber quien busca cita cuando solo hay servicios en lote."""
        lote = self._e.lotes.abierto
        return {
            "umbral_pct": round(100 * umbral_lote(self._e), 1),
            "ventana_s": int(self._cfg["ventana_segundos"]),
            "tamano_maximo": int(self._cfg["tamano_maximo"]),
            "abierto": lote is not None,
            "pendientes": len(lote.solicitudes) if lote else 0,
            "cierra_en": lote.cierra_en if lote else None,
        }

    # --- entrar al lote ---

    def entrar(self, estudiante_id: str, solicitud: dict, sesion_id: str | None = None, origen: str = "chat") -> dict:
        """Pone la solicitud en el lote abierto (lo abre si no hay). Solo vale si la búsqueda directa no tiene
        opciones y los servicios compatibles están en modo lote."""
        from .citas_service import CitasService

        solicitud = {**solicitud, "estudiante_id": estudiante_id}
        propuesta = CitasService(self._e).proponer(solicitud, 1)
        if propuesta.get("motivo_vacio") != "servicios_en_lote":
            detalle = (
                "Hay opciones directas: reserva una; el lote es solo para servicios con ocupación alta."
                if propuesta["opciones"]
                else "No hay cupos compatibles, ni siquiera en lote."
            )
            raise InvalidRequestError(detalle)

        repo = self._e.lotes
        ventana = int(self._cfg["ventana_segundos"])
        with repo.lock:
            lote = repo.abierto
            if lote and any(sl.estudiante_id == estudiante_id for sl in lote.solicitudes):
                raise YaEnLoteError(f"{estudiante_id} ya está esperando en el lote {lote.id}")
            nuevo = lote is None
            ahora = _ahora()
            if nuevo:
                lote = Lote(id=repo.nuevo_id(), abierto_en=_iso(ahora), cierra_en=_iso(ahora + timedelta(seconds=ventana)))
                repo.abierto = lote
                temporizador = threading.Timer(ventana, self.cerrar, args=(lote,))
                temporizador.daemon = True
                lote.timer = temporizador
                temporizador.start()
            entrada = SolicitudLote(
                estudiante_id, solicitud, sesion_id, len(lote.solicitudes) + 1, _iso(ahora), origen
            )
            lote.solicitudes.append(entrada)
            lleno = len(lote.solicitudes) >= int(self._cfg["tamano_maximo"])
            resumen = self._resumen(lote)
            para_estudiante = self.estado_para(lote, entrada)
            if sesion_id and (sesion := self._e.chats.obtener(sesion_id)):
                sesion.lote_id = lote.id

        self._actividad.lote_evento("lote_abierto" if nuevo else "lote_solicitud", resumen, estudiante_id, origen)
        self._e.avisos.agregar(estudiante_id, "lote_en_espera", {"lote_id": lote.id, "lote": para_estudiante})
        if lleno:  # se cierra solo al juntar el máximo; el genético no debe frenar esta respuesta
            threading.Thread(target=self.cerrar, args=(lote,), daemon=True).start()
        return {"ok": True, "lote": para_estudiante}

    # --- cierre y asignación ---

    def cerrar(self, lote: Lote) -> None:
        """Cierra el lote (la llama el temporizador o el tope de solicitudes) y lo resuelve con el genético."""
        repo = self._e.lotes
        with repo.lock:
            if repo.abierto is not lote or lote.estado != "abierto":
                return  # ya se cerró, o la demo se reinició y este lote dejó de existir
            lote.estado = "resolviendo"
            repo.abierto = None
            if lote.timer is not None:
                lote.timer.cancel()
        with self._e.lock:  # nadie reserva ni cancela mientras se asigna en conjunto
            try:
                self._resolver(lote)
            except Exception as error:  # noqa: BLE001 — el lote no puede quedar colgado
                lote.estado = "resuelto"
                lote.cerrado_en = _iso(_ahora())
                lote.resultado = {"error": f"{type(error).__name__}: {error}", "asignados": 0, "sin_cupo": len(lote.solicitudes)}
                repo.archivar(lote)
                for sl in lote.solicitudes:
                    self._avisar(sl, "lote_error", "No pude resolver el lote por un error del sistema. Intenta pedir tu cita de nuevo.")
                self._actividad.lote_evento("lote_resuelto", self._resumen(lote), None, "lote")

    def _resolver(self, lote: Lote) -> None:
        from .citas_service import CitasService

        motor = self._e.motor
        plan = motor.planificar_lote(
            [sl.solicitud for sl in lote.solicitudes],
            poblacion=int(self._cfg["poblacion"]),
            generaciones=int(self._cfg["generaciones"]),
            semilla=int(self._cfg["semilla"]),
        )
        por_clave = {sl.clave: sl for sl in lote.solicitudes}
        citas = CitasService(self._e)
        asignadas: list[tuple[SolicitudLote, dict, object]] = []
        sin_cupo: list[SolicitudLote] = [por_clave[c] for c in plan["sin_cupo"]]
        for a in plan["asignaciones"]:
            sl = por_clave[a["solicitud_id"]]
            ideal = self._e.tablas["motivo_a_servicio"].get(sl.solicitud.get("motivo", ""))
            try:
                cita = citas.reservar(sl.estudiante_id, a["opcion_id"], ideal, origen="lote")
            except PlatformError:  # no debería pasar (se asigna con el candado tomado); se trata como sin cupo
                sin_cupo.append(sl)
                continue
            asignadas.append((sl, a, cita))
        for sl in sin_cupo:
            citas.registrar_desencuentro(sl.solicitud, origen="lote")

        lote.resultado = {
            "asignados": len(asignadas),
            "sin_cupo": len(sin_cupo),
            "tiempo_s": plan["tiempo_s"],
            "poblacion": plan["poblacion"],
            "generaciones": plan["generaciones"],
            "genetico": plan["genetico"],
            "llegada": plan["llegada"],
            "mejora_sobre_llegada": plan["mejora_sobre_llegada"],
            "asignaciones": [
                {
                    "estudiante_id": sl.estudiante_id,
                    "posicion_llegada": sl.posicion,
                    "orden_asignacion": plan["orden"].index(sl.clave) + 1,
                    "servicio_nombre": a["servicio_nombre"],
                    "tipo_label": self._etiquetas.tipo(a["tipo"]),
                    "distrito": a["distrito"],
                    "fecha": a["fecha"],
                    "hora_inicio": a["hora_inicio"],
                    "hora_fin": a["hora_fin"],
                    "canal": a["canal"],
                    "canal_label": self._etiquetas.canal(a["canal"]),
                    "espera_dias": a["espera_dias"],
                    "es_alternativa": a["es_alternativa"],
                    "cita_id": cita.id,
                }
                for sl, a, cita in asignadas
            ],
            "sin_cupo_estudiantes": [sl.estudiante_id for sl in sin_cupo],
        }
        lote.estado = "resuelto"
        lote.cerrado_en = _iso(_ahora())
        self._e.lotes.archivar(lote)

        for sl, a, cita in asignadas:
            texto = (
                f"Tu lote se resolvió y quedaste con {a['servicio_nombre']} el {self._etiquetas.fecha_texto(a['fecha'])}, "
                f"de {a['hora_inicio']} a {a['hora_fin']} ({self._etiquetas.canal(a['canal']).lower()}). "
                f"Tu número de cita es {cita.id}."
            )
            self._avisar(sl, "lote_asignada", texto, cita=cita_out(cita).model_dump())
        for sl in sin_cupo:
            texto = (
                "Tu lote se resolvió, pero no quedó un cupo compatible con tus preferencias. Avisé al equipo de "
                "coordinación para ampliar la oferta. Si quieres, busco de nuevo con otros días u horarios."
            )
            self._avisar(sl, "lote_sin_cupo", texto)
        self._actividad.lote_evento("lote_resuelto", self._resumen(lote), None, "lote")

    def _avisar(self, sl: SolicitudLote, tipo: str, texto: str, cita: dict | None = None) -> None:
        """Aviso en vivo al estudiante y nota en su conversación (para que el agente sepa qué pasó)."""
        datos = {"mensaje": texto}
        if cita:
            datos["cita"] = cita
        self._e.avisos.agregar(sl.estudiante_id, tipo, datos)
        sesion = self._e.chats.obtener(sl.sesion_id) if sl.sesion_id else None
        if sesion is None:
            return
        sesion.lote_id = None
        candado = self._e.chats.candado(sesion.id)
        if candado.acquire(timeout=1):  # si el agente está respondiendo ahora, no se le pisa el historial
            try:
                from langchain_core.messages import AIMessage

                sesion.mensajes.append(AIMessage(texto))
            except ImportError:  # sin LangChain no hay chat que actualizar
                pass
            finally:
                candado.release()

    # --- vistas ---

    def estado_para(self, lote: Lote, sl: SolicitudLote) -> dict:
        """Lo que ve el estudiante mientras espera."""
        return {
            "id": lote.id,
            "estado": "en_espera",
            "posicion": sl.posicion,
            "solicitudes": len(lote.solicitudes),
            "tamano_maximo": int(self._cfg["tamano_maximo"]),
            "cierra_en": lote.cierra_en,
        }

    def _resumen(self, lote: Lote) -> dict:
        """El lote tal como viaja en los eventos de actividad."""
        r = lote.resultado
        resumen = None
        if r:
            resumen = {
                "asignados": r.get("asignados", 0),
                "sin_cupo": r.get("sin_cupo", 0),
                "tiempo_s": r.get("tiempo_s"),
                "espera_media": r.get("genetico", {}).get("espera_media"),
                "espera_media_llegada": r.get("llegada", {}).get("espera_media"),
                "mejora_sobre_llegada": r.get("mejora_sobre_llegada"),
                "error": r.get("error"),
            }
        return {
            "id": lote.id,
            "estado": "abierto" if lote.estado != "resuelto" else "resuelto",
            "solicitudes": len(lote.solicitudes),
            "tamano_maximo": int(self._cfg["tamano_maximo"]),
            "ventana_s": int(self._cfg["ventana_segundos"]),
            "cierra_en": lote.cierra_en if lote.estado != "resuelto" else None,
            "resultado": resumen,
        }

    def _detalle(self, lote: Lote) -> dict:
        e = self._etiquetas
        return {
            "id": lote.id,
            "estado": lote.estado,
            "abierto_en": lote.abierto_en,
            "cierra_en": lote.cierra_en,
            "cerrado_en": lote.cerrado_en,
            "solicitudes": [
                {
                    "posicion": sl.posicion,
                    "estudiante_id": sl.estudiante_id,
                    "entrada_en": sl.entrada_en,
                    "origen": sl.origen,
                    "motivo": sl.solicitud.get("motivo", ""),
                    "motivo_label": e.motivo(sl.solicitud.get("motivo", "")),
                    "distrito": sl.solicitud.get("distrito", ""),
                    "grupo": sl.solicitud.get("grupo", "diurno"),
                    "grupo_label": e.grupo(sl.solicitud.get("grupo", "diurno")),
                }
                for sl in lote.solicitudes
            ],
            "resultado": lote.resultado,
        }

    def panorama(self) -> dict:
        """Todo lo que muestra la pantalla Lotes de Coordinación."""
        _, _, por_servicio = embudo_por_servicio(self._e)
        servicios = []
        for s in self._e.motor.servicios():
            fila = por_servicio.get(s["service_id"], {"reservados": 0, "liberados": 0})
            servicios.append(
                {
                    "service_id": s["service_id"],
                    "nombre": s["nombre"],
                    "tipo": s["tipo"],
                    "tipo_label": self._etiquetas.tipo(s["tipo"]),
                    "distrito": s["distrito"],
                    "pct": porcentaje(fila["reservados"], fila["liberados"]),
                    "reservados": fila["reservados"],
                    "liberados": fila["liberados"],
                    "en_lote": en_lote(self._e, fila["reservados"], fila["liberados"]),
                }
            )
        servicios.sort(key=lambda s: (-s["pct"], s["service_id"]))
        repo = self._e.lotes
        with repo.lock:
            abierto = self._detalle(repo.abierto) if repo.abierto else None
            historial = [self._detalle(lote) for lote in repo.historial]
        return {
            "umbral_pct": round(100 * umbral_lote(self._e), 1),
            "ventana_s": int(self._cfg["ventana_segundos"]),
            "tamano_maximo": int(self._cfg["tamano_maximo"]),
            "servidor_ahora": _iso(_ahora()),
            "servicios": servicios,
            "abierto": abierto,
            "historial": historial,
        }
