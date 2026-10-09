"""Conversar con el agente desde la terminal, sin frontend (sirve para probar el modelo y las herramientas).

    python -m app.cli_chat                      # persona STU_DEMO_001
    python -m app.cli_chat --distrito DIST_GAIA --grupo diurno --modelo gemma4

Comandos: /nuevo (empieza otra conversación), /citas (lista las citas), /salir.
Usa los mismos servicios que POST /api/chat; arrancar tarda unos segundos (siembra la demo).
"""

import argparse
import os

from .settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--estudiante", default="STU_DEMO_001")
    parser.add_argument("--distrito", default=None)
    parser.add_argument("--grupo", choices=["diurno", "nocturno"], default=None)
    parser.add_argument("--modelo", default=None, help="Nombre del modelo en Ollama (por defecto AURA_OLLAMA_MODEL)")
    args = parser.parse_args()
    if args.modelo:
        os.environ["AURA_OLLAMA_MODEL"] = args.modelo

    from agente.agente import AgenteAura
    from agente.config import ConfigAgente

    from .services.chat_service import ChatService, estado_ollama
    from .services.errors import PlatformError
    from .services.siembra_service import crear_estado_sembrado

    config = ConfigAgente.desde_entorno()
    diagnostico = estado_ollama(config)
    print(f"Modelo: {config.modelo} · Ollama: {config.url} · {diagnostico['detalle']}")
    print("Preparando la demo…")
    estado = crear_estado_sembrado(Settings.desde_entorno())
    servicio = ChatService(estado, AgenteAura(config))
    print(f"Hoy (simulado): {estado.hoy}. Escribe tu mensaje. /nuevo, /citas, /salir.\n")

    sesion = None
    while True:
        try:
            texto = input("tú > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto:
            continue
        if texto == "/salir":
            break
        if texto == "/nuevo":
            sesion = None
            print("(conversación nueva)\n")
            continue
        if texto == "/citas":
            for c in estado.citas.list_by_student(args.estudiante):
                print(f"  {c.id} · {c.servicio_nombre} · {c.fecha} {c.hora_inicio} · {c.canal} · {c.estado}")
            print()
            continue
        try:
            r = servicio.conversar(texto, args.estudiante, sesion, args.distrito, args.grupo)
        except PlatformError as error:
            print(f"[{error.code}] {error.detalle}\n")
            continue
        sesion = r["session_id"]
        usadas = ", ".join(f"{h['nombre']}{'' if h['ok'] else ' (error)'}" for h in r["herramientas_usadas"])
        print(f"\nAURA > {r['respuesta']}")
        if usadas:
            print(f"  [herramientas: {usadas}]")
        for i, o in enumerate(r["opciones"], 1):
            alt = " (alternativa)" if o["es_alternativa"] else ""
            print(f"  {i}. {o['servicio_nombre']} · {o['fecha']} {o['hora_inicio']}-{o['hora_fin']} · {o['canal']}{alt}")
        if r["cita"]:
            print(f"  ✔ cita {r['cita'].id}")
        print()


if __name__ == "__main__":
    main()
