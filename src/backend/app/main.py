"""Punto de entrada: `uvicorn app.main:app --port 8080` (desde src/backend)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import academico, actividad, avisos, catalogo, chat, citas, coordinacion, lotes, demo, desencuentros, reglas, salud
from .repositories.app_state import AppState
from .services.errors import PlatformError
from .services.siembra_service import crear_estado_sembrado
from .settings import Settings


def create_app(
    settings: Settings | None = None, estado: AppState | None = None, agente=None
) -> FastAPI:
    """Crea la app; al arrancar construye y siembra el AppState (salvo que se inyecte uno).

    `agente` (opcional) reemplaza al agente de Ollama; se usa en las pruebas."""
    settings = settings or Settings.desde_entorno()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.estado = estado or crear_estado_sembrado(settings)
        app.state.agente = agente
        yield

    app = FastAPI(title="AURA API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(PlatformError)
    async def _error_de_plataforma(_: Request, error: PlatformError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.code, "detalle": error.detalle},
        )

    for router in (salud, demo, coordinacion, actividad, academico, lotes, avisos, desencuentros, reglas, catalogo, citas, chat):
        app.include_router(router.router)
    return app


app = create_app()
