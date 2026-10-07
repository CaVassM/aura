"""JSON Schema de las herramientas disponibles para el tool calling del agente."""


def _campo_solicitud() -> dict:
    """Describe los campos comunes que expresan una preferencia de cita."""
    return {
        "type": "object",
        "properties": {
            "estudiante_id": {"type": "string"},
            "motivo": {"type": "string"},
            "distrito": {"type": "string"},
            "franjas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dia": {"type": "string"},
                        "desde": {"type": "string"},
                        "hasta": {"type": "string"},
                    },
                    "required": ["dia", "desde", "hasta"],
                },
            },
            "canales_aceptables": {"type": "array", "items": {"type": "string"}},
            "grupo": {"type": "string", "enum": ["diurno", "nocturno"]},
            "fecha_solicitud": {"type": "string", "description": "Fecha ISO opcional"},
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


def esquemas_herramientas() -> list[dict]:
    """Entrega las cuatro declaraciones name/description/parameters para un LLM."""
    solicitud = _campo_solicitud()
    return [
        _herramienta(
            "proponer_opciones",
            "Propone citas compatibles sin reservarlas.",
            {
                "solicitud": solicitud,
                "k": {"type": "integer", "minimum": 1, "default": 3},
            },
            ["solicitud"],
        ),
        _herramienta(
            "reservar",
            "Reserva una opción si su cupo sigue libre.",
            {
                "estudiante_id": {"type": "string"},
                "opcion_id": {"type": "string"},
                "servicio_ideal": {
                    "type": "string",
                    "description": "Opcional: el servicio_ideal de la propuesta elegida",
                },
            },
            ["estudiante_id", "opcion_id"],
        ),
        _herramienta(
            "registrar_desencuentro",
            "Registra una solicitud sin opción compatible.",
            {"solicitud": solicitud},
            ["solicitud"],
        ),
        _herramienta(
            "cancelar_cita",
            "Cancela una cita y libera su cupo.",
            {"cita_id": {"type": "string"}},
            ["cita_id"],
        ),
    ]
