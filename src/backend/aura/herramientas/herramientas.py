"""Implementación de las cuatro funciones que el agente puede invocar."""

from datetime import date

from ..motor.datos import Solicitud
from ..motor.costo import costo_individual, mejores_opciones
from . import validacion
from .estado_agenda import AgendaViva

MAX_OPCIONES = 3  # tope de opciones por propuesta (`max_opciones` en parametros.yaml lo sobrescribe)
MENSAJE_LOTE = "Este servicio tiene mucha demanda; sus cupos se reparten en grupo. Te confirmo en unos segundos."


class HerramientasAgente:
    """Las cuatro herramientas del agente, sobre una agenda en RAM inyectada."""

    def __init__(self, agenda: AgendaViva | None = None):
        self.agenda = agenda or AgendaViva()

    def ejecutar(self, nombre: str, argumentos: dict | str | None) -> dict:
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
            argumentos = validacion.como_diccionario(argumentos or {}, "argumentos")
            return accion(**argumentos)
        except (TypeError, ValueError) as error:
            return {"ok": False, "error": "argumentos_invalidos", "detalle": str(error)}

    def convertir_solicitud(self, entrada: dict) -> tuple[Solicitud, str]:
        """Valida preferencias JSON y traduce el motivo usando tablas.yaml."""
        distritos = {servicio.distrito for servicio in self.agenda.servicios}
        return validacion.convertir_solicitud(
            entrada, self.agenda.hoy, self.agenda.tablas, distritos
        )

    def proponer_opciones(
        self,
        solicitud: dict,
        k: int = 3,
        excluir_servicios=None,
        servicios_lote=None,
        ventana_lote_s: int | None = None,
    ) -> dict:
        """Devuelve hasta `max_opciones` (3) propuestas válidas y disponibles, sin reservarlas.

        Orden: primero las del servicio que la persona pidió por nombre (`service_id_preferido` en la solicitud, un id o
        un nombre) o, si no pidió ninguno, las del tipo de servicio ideal; después las del tipo ideal; las alternativas
        afines solo completan si faltan. Dentro de cada grupo manda el costo; a igual costo, primero un cupo por servicio
        y los del distrito de la persona.

        `servicios_lote` son los servicios en modo lote: no se ofrecen cupo a cupo, sino como UNA opción de tipo `lote`
        por servicio (se ordena con el costo de su mejor cupo, como cualquier otra). `excluir_servicios` los aparta del
        todo. Toda respuesta trae `mensaje`: el texto del backend para los casos especiales, o None."""
        try:
            modelo, tipo_ideal = self.convertir_solicitud(solicitud)
            maximo = int(self.agenda.parametros.get("max_opciones", MAX_OPCIONES))
            k = min(max(1, int(k)), maximo)
            pedido = validacion.como_diccionario(solicitud, "solicitud")
            fecha = date.fromisoformat(str(pedido["fecha"])) if pedido.get("fecha") else None
        except (KeyError, ValueError, TypeError) as error:
            return {
                "opciones": [],
                "motivo_vacio": "solicitud_invalida",
                "detalle": str(error),
            }
        agenda = self.agenda
        consultado = str(pedido.get("service_id_preferido") or "").strip()
        preferidos = self.resolver_servicios(consultado) if consultado else []
        excluidos = frozenset(excluir_servicios or ())
        en_lote = frozenset(servicios_lote or ()) - excluidos
        # Un servicio puede tener varios cupos a la misma hora: para la persona son la misma opción. Se muestra una sola
        # por (servicio, fecha, hora, canal); al reservar se toma el cupo que quede. Un servicio en lote es una sola
        # opción, sin importar cuántos cupos tenga. `fecha` (opcional) limita las opciones a ese día concreto; las
        # franjas siguen mandando el día de la semana.
        candidatas = self._mejores(modelo, 2000, excluir=excluidos)
        entradas, vistas, cupos_lote = [], set(), {}
        for op in candidatas:
            cupo = agenda.cupo_por_id[op.cupo_id]
            if fecha is not None and cupo.fecha != fecha:
                continue
            if cupo.service_id in en_lote:
                cupos_lote[cupo.service_id] = cupos_lote.get(cupo.service_id, 0) + 1
                if cupos_lote[cupo.service_id] == 1:
                    entradas.append((op, cupo, True))
                continue
            clave = (cupo.service_id, cupo.fecha, cupo.hora_inicio, op.canal)
            if clave in vistas:
                continue
            vistas.add(clave)
            entradas.append((op, cupo, False))

        con_cupo = {cupo.service_id for _, cupo, _ in entradas}
        pedidos = [sid for sid in preferidos if sid in con_cupo]  # los que nombró la persona y sí tienen cupo

        def nivel(cupo) -> int:
            """0: lo que la persona pidió (servicio por nombre, o el tipo ideal); 1: el tipo ideal; 2: alternativas."""
            if pedidos:
                if cupo.service_id in pedidos:
                    return 0
            elif cupo.tipo == tipo_ideal:
                return 0
            return 1 if cupo.tipo == tipo_ideal else 2

        # Dentro de cada nivel manda el costo. Los costos empatan a menudo (misma fecha y canal): entonces va primero un
        # cupo por servicio (sin esto, el servicio con el id más bajo llenaba las 3 opciones con sus horas) y, a igual
        # ronda, los servicios del distrito de la persona.
        beta = float(agenda.parametros["beta"])
        rondas: dict[str, int] = {}
        claves = []
        for op, cupo, _ in entradas:
            ronda = rondas.get(cupo.service_id, 0)
            rondas[cupo.service_id] = ronda + 1
            costo = round(costo_individual(op, agenda.cupo_por_id, agenda.hoy, beta), 6)
            claves.append((nivel(cupo), costo, ronda, cupo.distrito != modelo.distrito))
        orden = sorted(range(len(entradas)), key=claves.__getitem__)  # estable: el resto del empate, como antes
        elegidas = [entradas[i] for i in orden[:k]]
        opciones = [
            self._formatear_lote(op, cupo, cupos_lote[cupo.service_id], tipo_ideal, ventana_lote_s)
            if es_lote
            else self._formatear_opcion(op, tipo_ideal)
            for op, cupo, es_lote in elegidas
        ]
        mensajes, preferido = [], None
        if consultado:
            preferido, aviso = self._informe_preferido(consultado, preferidos, pedidos, candidatas, en_lote, tipo_ideal)
            if aviso:
                mensajes.append(aviso)
        if not opciones:
            mensajes.append(
                "No encontré cupos dentro de los días, horarios y canales que puedes. Aviso al equipo de coordinación "
                "para que amplíe la oferta y, si quieres, te anoto en la lista de espera por si se libera un cupo."
            )
            return {
                "opciones": [],
                "motivo_vacio": "sin_cupos_compatibles",
                "servicio_ideal": tipo_ideal,
                "preferido": preferido,
                "mensaje": " ".join(mensajes),
                "sugerencia": (
                    "No ofrezcas otros días, horas ni canales que la persona no dijo. Registra el desencuentro y "
                    "ofrécele la lista de espera."
                ),
            }
        if any(o["tipo_opcion"] == "lote" for o in opciones):
            mensajes.append(MENSAJE_LOTE)
        return {
            "opciones": opciones,
            "servicio_ideal": tipo_ideal,
            "preferido": preferido,
            "mensaje": " ".join(mensajes) or None,
        }

    def resolver_servicios(self, referencia) -> list[str]:
        """Ids de servicio para un id o un nombre («Brújula», «Espacio Lumen Pares»); vacío si no coincide con ninguno."""
        texto = str(referencia or "").strip()
        if not texto:
            return []
        if texto.upper() in self.agenda.servicio_por_id:
            return [texto.upper()]
        plano = validacion._plano(texto)
        servicios = self.agenda.servicios
        iguales = [s.service_id for s in servicios if validacion._plano(s.nombre) == plano]
        if iguales:
            return iguales
        parecidos = [s.service_id for s in servicios if plano in validacion._plano(s.nombre)]
        if parecidos:
            return parecidos
        palabras = plano.split()
        return [s.service_id for s in servicios if palabras and all(p in validacion._plano(s.nombre) for p in palabras)]

    def lote_compatible(self, solicitud: dict, servicios_lote) -> list[str]:
        """Servicios en modo lote con al menos un cupo compatible con la solicitud (del más al menos conveniente)."""
        modelo, _ = self.convertir_solicitud(solicitud)
        en_lote = frozenset(servicios_lote or ())
        vistos: dict[str, None] = {}
        for op in self._mejores(modelo, 2000):
            sid = self.agenda.cupo_por_id[op.cupo_id].service_id
            if sid in en_lote:
                vistos.setdefault(sid)
        return list(vistos)

    def _texto_fecha(self, dia: date) -> str:
        etiquetas = self.agenda.tablas["etiquetas"]
        return f"{etiquetas['dias_semana_largo'][dia.weekday()]} {dia.day} de {etiquetas['meses'][dia.month - 1]}"

    def _informe_preferido(self, consultado, preferidos, con_cupo, candidatas, en_lote, tipo_ideal):
        """Qué pasó con el servicio que la persona nombró: `(datos, mensaje)`; el mensaje es None si todo va bien."""
        agenda = self.agenda
        if not preferidos:
            return (
                {"consultado": consultado, "encontrado": False},
                f"No encontré un servicio llamado «{consultado}». Te muestro las mejores opciones para ti.",
            )
        sid = (con_cupo or sorted(preferidos, key=lambda i: agenda.servicio_por_id[i].tipo != tipo_ideal))[0]
        servicio = agenda.servicio_por_id[sid]
        datos = {"consultado": consultado, "encontrado": True, "service_id": sid, "servicio_nombre": servicio.nombre}
        if con_cupo:
            return {**datos, "disponible": True}, None
        etiquetas = agenda.tablas["etiquetas"]
        datos |= {"disponible": False, "fecha_mas_cercana": None, "mejor_alternativa_mismo_tipo": None}
        partes = [f"No hay cupos en {servicio.nombre} dentro de los días, horarios y canales que puedes."]
        libres = agenda.cupos_libres_de(sid)
        if libres:
            primero = libres[0]
            datos["fecha_mas_cercana"] = {
                "fecha": primero.fecha.isoformat(),
                "hora_inicio": primero.hora_inicio.isoformat(timespec="minutes"),
                "hora_fin": primero.hora_fin.isoformat(timespec="minutes"),
            }
            partes.append(
                f"Su cupo más cercano es el {self._texto_fecha(primero.fecha)} a las "
                f"{primero.hora_inicio.isoformat(timespec='minutes')}, fuera de lo que puedes."
            )
        for op in candidatas:
            cupo = agenda.cupo_por_id[op.cupo_id]
            if cupo.tipo != servicio.tipo or cupo.service_id in preferidos:
                continue
            otro = agenda.servicio_por_id[cupo.service_id]
            datos["mejor_alternativa_mismo_tipo"] = (
                self._formatear_lote(op, cupo, 1, tipo_ideal, None)
                if cupo.service_id in en_lote
                else self._formatear_opcion(op, tipo_ideal)
            )
            tipo = etiquetas["tipo"].get(cupo.tipo, cupo.tipo).lower()
            if cupo.service_id in en_lote:
                partes.append(f"La mejor opción de {tipo} en otro servicio es {otro.nombre}, que reparte sus cupos por lote.")
            else:
                partes.append(
                    f"La mejor opción de {tipo} en otro servicio es {otro.nombre}, el {self._texto_fecha(cupo.fecha)} de "
                    f"{cupo.hora_inicio.isoformat(timespec='minutes')} a {cupo.hora_fin.isoformat(timespec='minutes')}."
                )
            break
        return datos, " ".join(partes)

    def _mejores(
        self, modelo: Solicitud, k: int, referencia: date | None = None, excluir: frozenset = frozenset()
    ) -> list:
        """Hasta k opciones válidas y libres de menor costo para la solicitud.

        `referencia` es la fecha desde la cual se cuentan cupos y espera (por defecto, hoy).
        """
        agenda = self.agenda
        referencia = referencia or agenda.hoy
        return mejores_opciones(
            modelo,
            agenda.opciones_validas(modelo, referencia),
            agenda.cupos_ocupados() | agenda.cupos_de_servicios(excluir),
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
        etiquetas = agenda.tablas["etiquetas"]
        return {
            "opcion_id": f"{cupo.id}|{opcion.canal}",
            "tipo_opcion": "cupo",
            "service_id": cupo.service_id,
            "servicio_nombre": servicio.nombre,
            "tipo": cupo.tipo,
            "distrito": cupo.distrito,
            "fecha": cupo.fecha.isoformat(),
            "dia_semana": etiquetas["dias_semana_largo"][cupo.fecha.weekday()],
            "hora_inicio": cupo.hora_inicio.isoformat(timespec="minutes"),
            "hora_fin": cupo.hora_fin.isoformat(timespec="minutes"),
            "canal": opcion.canal,
            "canal_label": etiquetas["canal"].get(opcion.canal, opcion.canal),
            "dias_espera": (cupo.fecha - agenda.hoy).days,
            "es_alternativa": cupo.tipo != tipo_ideal,
            "afinidad": opcion.afinidad,
        }

    def _formatear_lote(self, opcion, cupo, cupos_libres: int, tipo_ideal: str, ventana_s: int | None) -> dict:
        """Un servicio en modo lote como UNA opción: sin día ni hora (los decide el lote)."""
        servicio = self.agenda.servicio_por_id[cupo.service_id]
        return {
            "opcion_id": f"LOTE|{cupo.service_id}",
            "tipo_opcion": "lote",
            "service_id": cupo.service_id,
            "servicio_nombre": servicio.nombre,
            "tipo": cupo.tipo,
            "distrito": cupo.distrito,
            "cupos_libres": cupos_libres,
            "tiempo_respuesta_s": int(ventana_s if ventana_s is not None else 30),
            "es_alternativa": cupo.tipo != tipo_ideal,
            "afinidad": opcion.afinidad,
            "mensaje": MENSAJE_LOTE,
        }

    def reservar(
        self, estudiante_id: str, opcion_id: str, servicio_ideal: str | None = None
    ) -> dict:
        """Toma un cupo si todavía está libre y guarda el comprobante de cita en RAM.

        `servicio_ideal` (el `servicio_ideal` de la propuesta) es opcional.
        """
        return self.agenda.reservar(estudiante_id, opcion_id, servicio_ideal=servicio_ideal)

    def cancelar_cita(self, cita_id: str, estudiante_id: str | None = None) -> dict:
        """Cancela una cita viva y vuelve a liberar su cupo.

        Con `estudiante_id`, solo la puede cancelar su dueño (otra persona recibe `cita_no_encontrada`).
        """
        return self.agenda.cancelar(cita_id, estudiante_id)

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        """Guarda en RAM una solicitud sin opciones compatibles para su análisis operativo."""
        try:
            modelo, _ = self.convertir_solicitud(solicitud)
        except (KeyError, ValueError, TypeError) as error:
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
