"""Demo sin LLM del ciclo proponer, reservar, fallar, cancelar y registrar."""

from pathlib import Path
from tempfile import TemporaryDirectory

from aura.herramientas import herramientas as api
from aura.herramientas.estado_agenda import AgendaViva


def main() -> None:
    """Ejecuta las llamadas de herramientas y muestra sus respuestas JSON."""
    with TemporaryDirectory(prefix="aura_demo_") as temporal:
        api._AGENDA = AgendaViva(ruta_estado=Path(temporal) / "estado.json")
        solicitud = {
            "estudiante_id": "DEMO_001",
            "motivo": "academic_pressure",
            "distrito": "DIST_GAIA",
            "grupo": "diurno",
            "franjas": [{"dia": "Tue", "desde": "09:00", "hasta": "18:00"}],
            "canales_aceptables": ["digital", "phone"],
        }
        propuesta = api.proponer_opciones(solicitud, k=1)
        print("Propuesta:", propuesta)
        if propuesta["opciones"]:
            opcion_id = propuesta["opciones"][0]["opcion_id"]
            primera = api.reservar("DEMO_001", opcion_id)
            print("Reserva:", primera)
            print("Intento duplicado:", api.reservar("DEMO_002", opcion_id))
            print("Cancelación:", api.cancelar_cita(primera["cita"]["cita_id"]))
        nocturna = {
            "estudiante_id": "DEMO_NOCTURNO",
            "motivo": "academic_pressure",
            "distrito": "DIST_GAIA",
            "grupo": "nocturno",
            "franjas": [{"dia": "Tue", "desde": "19:00", "hasta": "21:00"}],
            "canales_aceptables": ["phone"],
        }
        alternativas = api.proponer_opciones(nocturna, k=3)
        print("Consejería nocturna:", alternativas)
        print("Registro de desencuentro:", api.registrar_desencuentro(nocturna))


if __name__ == "__main__":
    main()
