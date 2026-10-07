"""Fixtures de la API: un estado sembrado compartido (solo lectura) y uno fresco por prueba."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.siembra_service import crear_estado_sembrado
from app.settings import Settings


@pytest.fixture(scope="session")
def settings():
    return Settings.desde_entorno()


@pytest.fixture(scope="session")
def estado_sembrado(settings):
    """Estado de la demo sembrado una sola vez; las pruebas que lo usan no deben escribir."""
    return crear_estado_sembrado(settings)


@pytest.fixture(scope="session")
def client(estado_sembrado, settings):
    with TestClient(create_app(settings, estado_sembrado)) as cliente:
        yield cliente


@pytest.fixture()
def estado_fresco(settings):
    """Estado propio de la prueba, para las que reservan, cancelan o reinician."""
    return crear_estado_sembrado(settings)


@pytest.fixture()
def client_fresco(estado_fresco, settings):
    with TestClient(create_app(settings, estado_fresco)) as cliente:
        yield cliente
