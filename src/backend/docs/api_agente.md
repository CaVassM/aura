# API del agente conversacional (estudiante)

El agente AURA conversa con la persona, entiende el motivo, reúne sus preferencias y usa las herramientas de la agenda para **proponer, reservar y cancelar citas**. Funciona con **LangChain + Ollama** (modelo local, por defecto `gemma4`). Todo el estado (conversaciones y citas) vive en RAM, igual que el resto del backend.

Prefijo `/api`. Errores: `{"error": "<código>", "detalle": "<texto>"}`.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/chat` | Enviar un mensaje y recibir la respuesta del agente |
| GET | `/chat/{session_id}?estudiante_id=` | Releer la conversación (para repintar el chat al recargar) |
| DELETE | `/chat/{session_id}?estudiante_id=` | Borrar la conversación (no cancela citas ya reservadas) |
| GET | `/chat/estado` | Diagnóstico: ¿hay dependencias, responde Ollama, está el modelo? |

Las citas reservadas por el chat son las mismas de `GET /appointments?estudiante_id=` y se ven en Coordinación.

### `POST /chat`

Cuerpo (JSON):

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `mensaje` | string (1–2000) | sí | Lo que escribe la persona |
| `estudiante_id` | string | sí | Identificador de la persona. **El agente lo usa como dueño de las citas; el modelo no puede cambiarlo** |
| `session_id` | string | no | Omítelo en el primer mensaje; en los siguientes reenvía el que devolvió la respuesta. Si no existe o es de otra persona: `404` |
| `distrito` | string | no | Ej. `DIST_GAIA`. Si el portal ya lo conoce, el agente no lo pregunta. Distritos: `DIST_GAIA`, `DIST_NEBULA`, `DIST_VECTOR`, `DIST_HORIZON`, `DIST_QUANTUM` (otro valor: `422`) |
| `grupo` | `diurno` \| `nocturno` | no | Turno de la persona. Si no se envía, el agente asume `diurno` |

`distrito` y `grupo` se recuerdan en la sesión; basta enviarlos una vez.

```json
{
  "mensaje": "Estoy muy estresada por los parciales, ¿puedo hablar con alguien el miércoles en la tarde por videollamada?",
  "estudiante_id": "STU_DEMO_001",
  "distrito": "DIST_GAIA",
  "grupo": "diurno"
}
```

Respuesta `200`:

| Campo | Tipo | Descripción |
|---|---|---|
| `session_id` | string | Guárdalo y reenvíalo en el siguiente mensaje |
| `respuesta` | string | Texto del agente para la burbuja |
| `opciones` | lista | Si el agente **acaba de proponer** citas: tarjetas para mostrar (mismos campos que `OpcionOut` de `POST /appointments/proposals`). **No hay nada reservado todavía**: la persona elige escribiendo (o el portal envía «la opción 2» como mensaje) |
| `cita` | objeto \| null | Cita reservada en este mensaje (mismo formato que `CitaOut` de `/appointments`) |
| `cita_cancelada` | objeto \| null | Cita cancelada en este mensaje |
| `desencuentro_registrado` | bool | El agente avisó al equipo que no había opción compatible |
| `alerta_crisis` | bool | El mensaje activó el protocolo de ayuda inmediata (la respuesta es un texto fijo con líneas de ayuda; no se llamó al modelo) |
| `herramientas_usadas` | lista | `[{"nombre": "proponer_opciones", "ok": true}, …]`, en orden. Útil para depurar |

```json
{
  "session_id": "5f0c1d…",
  "respuesta": "Entiendo, los parciales pesan. Encontré estas opciones para el miércoles por la tarde: …",
  "opciones": [{
    "opcion_id": "C0000321|digital", "service_id": "SRV_AE_001", "servicio_nombre": "Espacio Brújula Orientación",
    "tipo": "counseling", "tipo_label": "Consejería", "distrito": "DIST_GAIA",
    "fecha": "2026-11-18", "hora_inicio": "14:00", "hora_fin": "15:00", "canal": "digital",
    "dias_espera": 3, "es_alternativa": false, "afinidad": 1.0
  }],
  "cita": null, "cita_cancelada": null, "desencuentro_registrado": false,
  "alerta_crisis": false,
  "herramientas_usadas": [{"nombre": "proponer_opciones", "ok": true}]
}
```

Errores: `404 no_encontrado` (sesión ajena o inexistente), `422` (cuerpo inválido o distrito desconocido), `503 agente_no_disponible` (Ollama apagado, modelo sin descargar o dependencias sin instalar; el `detalle` dice qué hacer).

Un mensaje tarda de unos segundos a más de un minuto según el equipo (cada herramienta es otra llamada al modelo): el frontend debe mostrar «AURA está escribiendo…» y no fijar un timeout menor a 2 minutos.

### `GET /chat/{session_id}`

Parámetro obligatorio `estudiante_id` (query). Devuelve `{"session_id", "mensajes": [{"rol": "user"|"agent", "texto"}]}` sin las llamadas a herramientas.

### `DELETE /chat/{session_id}`

Parámetro obligatorio `estudiante_id` (query). Devuelve `{"ok": true}`.

### `GET /chat/estado`

Sin parámetros.

```json
{"modelo": "gemma4", "url": "http://localhost:11434", "dependencias_instaladas": true,
 "ollama_disponible": true, "modelo_instalado": true, "detalle": "Listo."}
```

## Herramientas que usa el agente

El modelo las llama solo; no son endpoints. Están en `agente/herramientas.py` y llegan a la agenda a través de `CitasService` (igual que la API de citas).

| Herramienta | Parámetros que elige el modelo | Qué hace |
|---|---|---|
| `proponer_opciones` | `motivo`, `franjas` [{`dia` Mon–Sun, `desde`, `hasta` HH:MM}], `canales_aceptables` (`digital`, `phone`, `in_person`), `distrito`\*, `grupo`\*, `k` (1–5) | Busca hasta `k` citas compatibles. No reserva |
| `reservar_cita` | `numero` (1, 2, 3… de la última lista) | Reserva esa opción. El modelo nunca ve ni copia identificadores internos |
| `cancelar_cita` | `cita_id` | Cancela una cita **de esa persona** |
| `listar_mis_citas` | — | Lista las citas de la persona |
| `registrar_desencuentro` | — | Avisa que no hubo opción: guarda la última búsqueda (solo después de `proponer_opciones`) |

`proponer_opciones` se **niega a buscar** (`faltan_datos`) si en la conversación la persona no ha mencionado días ni canal (`agente/entrada.py`; basta una mención, incluso «cualquier día» o «da igual»). Es una red de seguridad contra modelos pequeños que inventan esos datos; el agente debe preguntárselos (tolera letras repetidas por error de tipeo). Del mismo modo, `cancelar_cita` se niega (`falta_confirmacion`) si el mensaje no pide cancelar ni responde «sí» a una pregunta de cancelar. Cada opción llega al modelo con un `texto` ya redactado (servicio, día, fecha, hora y canal) para que lo copie.

\* Opcionales si ya se enviaron en `POST /chat`. Si no hay distrito, el agente lo pregunta.

`estudiante_id` **no** es parámetro de ninguna herramienta: sale de la sesión. Motivos válidos: `academic_pressure`, `sleep_and_routine`, `social_support`, `career_concern`, `preventive_guidance`, `service_navigation` (su servicio ideal está en `config/tablas.yaml`).

## Instalar y probar en tu PC

Requisitos: Python 3.10+, [Ollama](https://ollama.com) con el modelo descargado (`ollama pull gemma4`; usa el nombre exacto de `ollama list`) y una versión reciente de Ollama (el soporte de herramientas de Gemma 4 se corrigió en versiones recientes).

```powershell
# desde src/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-agente.txt        # incluye requirements.txt
Copy-Item .env.example .env                   # opcional: cambia AURA_OLLAMA_MODEL si tu modelo se llama distinto

ollama serve                                  # si Ollama no está abierto ya
uvicorn app.main:app --reload --port 8080     # Swagger: http://localhost:8080/docs
```

Sin frontend, desde la terminal: `python -m app.cli_chat --distrito DIST_GAIA` (muestra también qué herramientas llamó el modelo).

Si el backend arranca sin `requirements-agente.txt`, todo funciona excepto `/api/chat`, que responde `503` con el comando de instalación.

### Variables de entorno (todas opcionales)

| Variable | Por defecto | Para qué |
|---|---|---|
| `AURA_OLLAMA_MODEL` | `gemma4` | Nombre del modelo en Ollama |
| `AURA_OLLAMA_URL` | `http://localhost:11434` | Servidor de Ollama |
| `AURA_OLLAMA_TEMPERATURE` | `0.2` | Baja para que use las herramientas de forma estable |
| `AURA_OLLAMA_NUM_CTX` | `8192` | Contexto en tokens (el de Ollama por defecto es corto para prompt + herramientas) |
| `AURA_OLLAMA_TIMEOUT` | `120` | Segundos de espera por respuesta del modelo |
| `AURA_OLLAMA_REASONING` | vacío | `false` apaga el «pensar» del modelo (más rápido); `true` lo enciende; vacío usa el comportamiento del modelo |
| `AURA_OLLAMA_KEEP_ALIVE` | `30m` | Tiempo que el modelo queda cargado en memoria sin uso |
| `AURA_AGENTE_MAX_PASOS` | `10` | Llamadas al modelo por mensaje antes de rendirse |
| `AURA_AGENTE_MAX_TURNOS` | `12` | Mensajes de la persona que recuerda el agente |

## Cómo está armado

```text
POST /api/chat → app/api/chat.py → ChatService (sesión, resultado) → agente.AgenteAura
                                        │                               │  prompt + LangChain create_agent
                                        └── PuertoPlataforma ◄──────────┘  herramientas (agente/herramientas.py)
                                             └─ CitasService → motor (aura.servicio.ServicioAsignacion)
```

- `agente/` no importa `app/` ni `aura/`: usa el puerto `agente/puerto.py`, que implementa `app/services/chat_service.py`.
- Seguridad: crisis (`agente/crisis.py`) responde con texto fijo sin llamar al modelo; el prompt prohíbe diagnosticar; las herramientas no dejan reservar ids inventados ni cancelar citas ajenas.
- Pruebas (no necesitan Ollama): `python -m pytest tests/test_agente_chat.py tests/test_agente_ollama_http.py tests/test_validacion_herramientas.py`. Usan un modelo guionado y un servidor que imita la API HTTP de Ollama; **no validan la calidad de las respuestas de gemma4**, eso se prueba conversando (`python -m app.cli_chat`).
