"""JSON Schema de las herramientas disponibles para el tool calling del agente.

Las descripciones y los `enum` están pensados para modelos pequeños: cuanto más cerrado el
valor, menos se inventa. Si se pasan `distritos` y `motivos`, salen como `enum`.
"""

from .validacion import CANALES, GRUPOS

DIAS_ISO = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _campo_solicitud(distritos: list[str] | None = None, motivos: list[str] | None = None) -> dict:
    """Describe los campos comunes que expresan una preferencia de cita."""
    distrito = {"type": "string", "description": "Distrito de la persona (para citas presenciales)"}
    if distritos:
        distrito["enum"] = list(distritos)
    motivo = {
        "type": "string",
        "description": (
            "Motivo de consulta: academic_pressure (presión académica), sleep_and_routine (sueño y "
            "rutina), social_support (apoyo social), career_concern (inquietud vocacional), "
            "preventive_guidance (orientación preventiva) o service_navigation (conocer los servicios)"
        ),
    }
    if motivos:
        motivo["enum"] = list(motivos)
    return {
        "type": "object",
        "properties": {
            "estudiante_id": {"type": "string", "description": "Identificador de la persona"},
            "motivo": motivo,
            "distrito": distrito,
            "franjas": {
                "type": "array",
                "minItems": 1,
                "description": "Días y rangos de hora en que la persona puede asistir",
                "items": {
                    "type": "object",
                    "properties": {
                        "dia": {"type": "string", "enum": DIAS_ISO},
                        "desde": {"type": "string", "description": "Hora de inicio HH:MM (24 h)"},
                        "hasta": {"type": "string", "description": "Hora de fin HH:MM (24 h)"},
                    },
                    "required": ["dia", "desde", "hasta"],
                },
            },
            "canales_aceptables": {
                "type": "array",
                "minItems": 1,
                "description": "digital = videollamada, phone = teléfono, in_person = presencial",
                "items": {"type": "string", "enum": list(CANALES)},
            },
            "grupo": {
                "type": "string",
                "enum": list(GRUPOS),
                "description": "diurno o nocturno (turno en que estudia la persona)",
            },
            "fecha_solicitud": {
                "type": "string",
                "description": "Fecha ISO AAAA-MM-DD; opcional, por defecto hoy",
            },
        },
        "required": [
            "estudiante_id",
            "motivo",
            "distrito",
            "franjas",
            "canales_aceptables",
            "grupo",
        ],
        "additionalProperties": False,
    }


def _herramienta(
    nombre: str, descripcion: str, propiedades: dict, obligatorios: list[str]
) -> dict:
    """Construye la envoltura estándar de una herramienta para el proveedor LLM."""
    return {
        "name": nombre,
        "description": descripcion,
        "parameters": {
            "type": "object",
            "properties": propiedades,
            "required": obligatorios,
            "additionalProperties": False,
        },
    }


def esquemas_herramientas(
    distritos: list[str] | None = None, motivos: list[str] | None = None
) -> list[dict]:
    """Entrega las cuatro declaraciones name/description/parameters para un LLM."""
    solicitud = _campo_solicitud(distritos, motivos)
    return [
        _herramienta(
            "proponer_opciones",
            "Busca citas compatibles con las preferencias de la persona y devuelve hasta k opciones "
            "ordenadas de mejor a peor. No reserva ni retiene el cupo. Si no hay opciones, devuelve "
            "`motivo_vacio` y una `sugerencia`.",
            {
                "solicitud": solicitud,
                "k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 3,
                    "description": "Cuántas opciones devolver",
                },
            },
            ["solicitud"],
        ),
        _herramienta(
            "reservar",
            "Reserva una opción que entregó proponer_opciones, solo después de que la persona la haya "
            "elegido. Falla con cupo_ya_tomado si otra persona lo tomó antes.",
            {
                "estudiante_id": {"type": "string"},
                "opcion_id": {
                    "type": "string",
                    "description": "El `opcion_id` exacto de la opción elegida, p. ej. C0000123|digital",
                },
                "servicio_ideal": {
                    "type": "string",
                    "description": "Opcional: el `servicio_ideal` de la propuesta elegida",
                },
            },
            ["estudiante_id", "opcion_id"],
        ),
        _herramienta(
            "registrar_desencuentro",
            "Registra una solicitud para la que no hubo ninguna opción compatible, de modo que el "
            "equipo de coordinación pueda ampliar la oferta. Úsala solo después de proponer_opciones.",
            {"solicitud": solicitud},
            ["solicitud"],
        ),
        _herramienta(
            "cancelar_cita",
            "Cancela una cita y libera su cupo. Con estudiante_id solo la puede cancelar su dueño.",
            {
                "cita_id": {"type": "string", "description": "Identificador, p. ej. CITA-0000001"},
                "estudiante_id": {
                    "type": "string",
                    "description": "Recomendado: la persona que cancela; debe ser la dueña de la cita",
                },
            },
            ["cita_id"],
        ),
    ]
