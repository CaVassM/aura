"""Repositorios en memoria (sin base de datos)."""

from .app_state import AppState, construir_estado
from .cita_repository import CitaRepository

__all__ = ["AppState", "CitaRepository", "construir_estado"]
