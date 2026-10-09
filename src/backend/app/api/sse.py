"""Flujo Server-Sent Events genérico sobre un registro con `epoca`, `ultimo_id` y `desde(ultimo)`."""

import asyncio
import json
import time

PING_CADA_S = 15
SONDEO_S = 0.3


def sse(evento: str, datos: dict, id_evento: int | None = None) -> str:
    cabecera = f"id: {id_evento}\n" if id_evento is not None else ""
    return f"{cabecera}event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


async def flujo(obtener_registro, desde: int, evento: str, desconectado=None, ping_cada_s: float = PING_CADA_S):
    """Genera el texto del flujo SSE.

    `obtener_registro` devuelve el registro vigente (al reiniciar la demo se reemplaza); `desconectado` es una
    corrutina que dice si el cliente se fue. Manda `inicio` al conectar, un evento por cada novedad, `reinicio` si
    el registro cambia de época y un comentario `: ping` para mantener viva la conexión."""
    repo = obtener_registro()
    epoca = repo.epoca
    reinicio = desde > repo.ultimo_id  # el cliente vio otra ejecución (el backend o la demo se reiniciaron)
    ultimo = 0 if reinicio else desde
    yield "retry: 2000\n\n"
    yield sse("inicio", {"epoca": epoca, "ultimo_id": repo.ultimo_id, "reinicio": reinicio})
    ultimo_ping = time.monotonic()
    while True:
        if desconectado is not None and await desconectado():
            return
        repo = obtener_registro()
        if repo.epoca != epoca:
            epoca, ultimo = repo.epoca, 0
            yield sse("reinicio", {"epoca": epoca})
        nuevos = repo.desde(ultimo)
        for e in nuevos:
            ultimo = e["id"]
            yield sse(evento, e, e["id"])
            ultimo_ping = time.monotonic()
        if not nuevos and time.monotonic() - ultimo_ping >= ping_cada_s:
            yield ": ping\n\n"
            ultimo_ping = time.monotonic()
        await asyncio.sleep(SONDEO_S)


CABECERAS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
