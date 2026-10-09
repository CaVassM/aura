"""El camino real de ChatOllama contra un servidor que imita la API HTTP de Ollama (/api/chat y /api/tags).

No prueba a gemma4: prueba que nuestras herramientas y mensajes se serializan como Ollama los espera
y que el bucle herramienta → respuesta funciona de punta a punta.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("langchain")
pytest.importorskip("langchain_ollama")

from fastapi.testclient import TestClient

from agente.agente import AgenteAura
from agente.config import ConfigAgente
from app.main import create_app

PEDIDOS: list[dict] = []


class FalsoOllama(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencio
        pass

    def _enviar(self, *lineas: dict):
        cuerpo = ("\n".join(json.dumps(l) for l in lineas) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        self._enviar({"models": [{"name": "gemma4:latest"}]})

    def do_POST(self):
        pedido = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        PEDIDOS.append(pedido)
        mensajes = pedido["messages"]
        base = {"model": pedido["model"], "created_at": "2026-01-01T00:00:00Z"}
        if mensajes[-1]["role"] == "tool":
            opciones = json.loads(mensajes[-1]["content"])["opciones"]
            texto = f"Encontré {len(opciones)} opciones para ti."
            return self._enviar(
                {**base, "message": {"role": "assistant", "content": texto}, "done": False},
                {**base, "message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop"},
            )
        llamada = {
            "function": {
                "name": "proponer_opciones",
                "arguments": {
                    "motivo": "academic_pressure",
                    "franjas": [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}],
                    "canales_aceptables": ["digital"],
                    "distrito": "DIST_GAIA",
                },
            }
        }
        self._enviar(
            {**base, "message": {"role": "assistant", "content": "", "tool_calls": [llamada]}, "done": False},
            {**base, "message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop"},
        )


@pytest.fixture()
def ollama_falso():
    servidor = HTTPServer(("127.0.0.1", 0), FalsoOllama)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    PEDIDOS.clear()
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()


def test_chat_de_punta_a_punta_con_chatollama(settings, estado_fresco, ollama_falso, monkeypatch):
    monkeypatch.setenv("AURA_OLLAMA_URL", ollama_falso)
    monkeypatch.setenv("AURA_OLLAMA_REASONING", "false")
    monkeypatch.setenv("AURA_OLLAMA_KEEP_ALIVE", "45m")
    config = ConfigAgente.desde_entorno()
    with TestClient(create_app(settings, estado_fresco, agente=AgenteAura(config))) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": "Tengo parciales y estoy agobiada, puedo el miércoles por videollamada", "estudiante_id": "E1"})
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert cuerpo["respuesta"].startswith("Encontré") and cuerpo["opciones"]
        estado = cliente.get("/api/chat/estado").json()
    assert estado["ollama_disponible"] and estado["modelo_instalado"]

    primero = PEDIDOS[0]
    assert primero["model"] == "gemma4" and primero["options"]["num_ctx"] == config.num_ctx
    assert primero["think"] is False and primero["keep_alive"] == "45m"
    assert {t["function"]["name"] for t in primero["tools"]} == {
        "proponer_opciones", "reservar_cita", "cancelar_cita", "listar_mis_citas", "registrar_desencuentro", "entrar_a_lote",
    }
    assert primero["messages"][0]["role"] == "system" and "AURA" in primero["messages"][0]["content"]
    assert primero["messages"][-1] == {"role": "user", "content": "Tengo parciales y estoy agobiada, puedo el miércoles por videollamada"}
    # el modelo no puede elegir el estudiante: ningún esquema lo pide
    assert "estudiante_id" not in json.dumps([t["function"]["parameters"] for t in primero["tools"]])
