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
| `distrito` | string | no | Distrito donde vive la persona, p. ej. `DIST_GAIA`; se usa para citas presenciales. Si el portal ya lo conoce, el agente no lo pregunta; durante la conversación la persona puede cambiarlo («esta semana estoy por Vector») y el cambio queda para la sesión. Distritos: `DIST_GAIA`, `DIST_NEBULA`, `DIST_VECTOR`, `DIST_HORIZON`, `DIST_QUANTUM` (otro valor: `422`) |
| `grupo` | `diurno` \| `nocturno` | no | Turno en que estudia. Normalmente **no se envía**: el agente lo toma de lo que la persona cuente (y lo guarda en la sesión); si no lo dijo, lo infiere de las horas que pide (todo desde las 18:00 → `nocturno`) o asume `diurno`, sin guardarlo |

`distrito` y `grupo` se recuerdan en la sesión; basta enviarlos una vez. El portal debería avisar al abrir el chat qué distrito usa (el frontend lo hace en el saludo).

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
| `opciones` | lista | Si el agente **acaba de proponer** citas: tarjetas para mostrar (mismos campos que `OpcionOut` de `POST /appointments/proposals`). **No hay nada reservado todavía**: la persona elige escribiendo, o el portal envía «quiero la opción 2» como mensaje al tocar una tarjeta (la numeración es el orden de la lista `opciones`, desde 1) |
| `cita` | objeto \| null | Cita reservada en este mensaje (mismo formato que `CitaOut` de `/appointments`: `id`, `servicio_nombre`, `tipo`, `tipo_label`, `distrito`, `hora_fin`, `slot.fecha_iso`, `canal`, `estado`) |
| `cita_cancelada` | objeto \| null | Cita cancelada en este mensaje |
| `desencuentro_registrado` | bool | El agente avisó al equipo que no había opción compatible |
| `lote_oferta` | objeto \| null | Todo lo compatible está en servicios en **modo lote** (≥ 75 % de utilización): no hay `opciones`; se ofrece entrar al lote. `{umbral_pct, ventana_s, tamano_maximo, abierto, pendientes, cierra_en, servicios[]}`. El portal puede mostrar un botón «Entrar al lote» que envía «sí, quiero entrar al lote» |
| `lote` | objeto \| null | La persona quedó esperando en un lote: `{id, estado: "en_espera", posicion, solicitudes, tamano_maximo, cierra_en}`. `cierra_en` (ISO UTC) sirve para la cuenta regresiva; el lote se cierra solo |
| `alerta_crisis` | bool | El mensaje activó el protocolo de ayuda inmediata (la respuesta es un texto fijo que remite a emergencias y a la línea de ayuda de la institución; no se llamó al modelo) |
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
| `proponer_opciones` | `motivo`, `franjas` [{`dia` Mon–Sun, `desde`, `hasta` HH:MM}], `canales_aceptables` (`digital`, `phone`, `in_person`), `distrito`\*, `grupo`\*, `fecha` (AAAA-MM-DD, solo si la persona pidió una fecha concreta), `k` (1–5) | Busca hasta `k` citas compatibles, una por servicio/fecha/hora/canal. Con `fecha` solo trae ese día; si no hay cupos ese día, trae las fechas más cercanas y le indica al modelo que lo diga. No reserva. Repetir la misma búsqueda en un mensaje devuelve `busqueda_repetida` |
| `reservar_cita` | `numero` (1, 2, 3… de la última lista) | Reserva esa opción. El modelo nunca ve ni copia identificadores internos |
| `cancelar_cita` | `cita_id` | Cancela una cita **de esa persona** |
| `listar_mis_citas` | — | Lista las citas de la persona |
| `entrar_a_lote` | — | Pone a la persona en el lote abierto (lo abre si no hay). Solo después de `proponer_opciones` → `servicios_en_lote` **y** si la persona aceptó (mismo tipo de bloqueo que cancelar) |
| `consultar_asistencia` | — | Lee la **asistencia a clases** de la persona (período actual, anterior y por curso). Es el **único** dato académico que ve el agente; se niega (`no_pidio_asistencia`) si la persona no habló de su asistencia o sus faltas |
| `avisarme_si_hay_cupo` | — | Anota a la persona en la **lista de espera** con su última búsqueda. Solo cuando no hubo opciones (o rechazó todas) **y** la persona aceptó que le avise (mismo bloqueo `falta_confirmacion`) |
| `registrar_desencuentro` | — | Avisa que no hubo opción: guarda la última búsqueda (solo después de `proponer_opciones`) |

`proponer_opciones` se **niega a buscar** (`faltan_datos`) si en la conversación la persona no ha mencionado días ni canal (`agente/entrada.py`; basta una mención, incluso «cualquier día» o «da igual»). Es una red de seguridad contra modelos pequeños que inventan esos datos; el agente debe preguntárselos (tolera letras repetidas por error de tipeo). Del mismo modo, `cancelar_cita` se niega (`falta_confirmacion`) si el mensaje no pide cancelar ni responde «sí» a una pregunta de cancelar. Cada opción llega al modelo con un `texto` ya redactado (servicio, día, fecha, hora y canal) para que lo copie.

\* Opcionales si ya se enviaron en `POST /chat`. Si no hay distrito, el agente lo pregunta.

`estudiante_id` **no** es parámetro de ninguna herramienta: sale de la sesión. Motivos válidos: `academic_pressure`, `sleep_and_routine`, `social_support`, `career_concern`, `preventive_guidance`, `service_navigation` (su servicio ideal está en `config/tablas.yaml`).

### Asistencia: lo único académico que ve el agente

`consultar_asistencia` devuelve solo `periodo`, `asistencia_actual`, `asistencia_periodo_anterior`, `variacion`, `minimo_requerido` y, por curso, `curso`, `asistencia`, `faltas`, `de_sesiones` y `bajo_el_minimo`. **No** hay notas, créditos, docentes, alertas ni encuesta D1 (la regla ya documentada en [como_funciona.md §2](como_funciona.md): D1 no se entrega al agente; de lo académico, solo la asistencia, que es la señal S2 del aviso). Para el agente no es un diagnóstico: el prompt le pide contar las cifras en simple, no hablar de riesgo ni de avisos, y ofrecer una cita de bienestar si le preocupa. Está implementado en `AcademicoService.asistencia_para_agente` y `PuertoPlataforma.asistencia`; los datos son simulados (ver abajo) y solo existen para los perfiles de la demo (`STU_DEMO_001…004`): para otra persona devuelve `sin_datos_academicos`.

## Vida académica del campus (cursos, calificaciones, calendario)

Alimentan las páginas `Mis cursos`, `Calificaciones` y `Calendario` del campus. **Simulado** (ni D1 ni D7 traen cursos, horarios ni notas): se inventa para los cuatro perfiles de la demo en `app/repositories/academico_repository.py`. Lo único real es el **calendario D7**: período `PER_2026_4` (5 oct – 23 dic), semanas de evaluación y actividades, filtrados por la institución y el distrito de la persona (`ALL` o el suyo: la pausa de bienestar es solo de Gaia; el encuentro estudiantil, solo de su institución y distrito). Estos endpoints son de lectura y los usa el frontend, no el agente.

| Método | Ruta | Devuelve |
|---|---|---|
| GET | `/api/estudiantes/{id}/academico/cursos` | `periodo` (semana, avance, evaluación en curso/próxima), `asistencia` (tasa, anterior, variación), `cursos[]` (horario, docente, aula, asistencia, promedio parcial, próxima evaluación) |
| GET | `/api/estudiantes/{id}/academico/calificaciones` | `escala` (1,0–7,0; aprueba 4,0), `promedio_general` y `variacion` (vs. período anterior), `cursos[]` con `evaluaciones[]` (nota, peso, estado `calificada`/`sin_publicar`/`programada`), `nota_necesaria` y `situacion` |
| GET | `/api/estudiantes/{id}/academico/calendario` | `eventos[]`: eventos D7 (`periodo_inicio`, `periodo_fin`, `semana_evaluacion`, `bienestar`, `actividad_universitaria`), `clase` (con `estado` `asistio`/`falto`/`programada`) y `evaluacion` |

`404 no_encontrado` si la persona no es un perfil de la demo. «Hoy» es el de la demo (`GET /api/demo/estado`, 15 nov 2026, último día de las evaluaciones intermedias).

Supuestos de la simulación (no salen de los datos): sin clases en las semanas de evaluación de D7; los exámenes parciales y finales caen dentro de esas semanas; asistencia mínima de **70 %**; escala 1,0–7,0 como `average_grade` de D3 y aprobación en 4,0; las inasistencias y notas son inventadas (Lucía y Diego tienen caída de asistencia frente al período anterior, para ilustrar la señal S2; Mateo y Valentina no).

## Lista de espera y aviso proactivo

**Lista de espera.** Si no hay cupo, el agente registra el desencuentro y pregunta si quiere que le avise; si dice que sí, queda anotada. Cada vez que se **cancela una cita** (lo único que libera cupos) se revisa la lista en orden de llegada: a quien le sirva un cupo libre (sin contar servicios en modo lote) le llega un aviso `cupo_disponible` por `/avisos/stream` con la opción lista para tocar, y la opción queda como «opción 1» de su conversación. No retiene el cupo: avisa y la persona decide; un mismo cupo se avisa a una sola persona. En Coordinación aparece en *En vivo* (`lista_espera_alta` y `lista_espera_aviso`).

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/api/appointments/lista-espera` | Anotarse por API (cuerpo como `proposals`); repetir la misma no la duplica |
| GET | `/api/estudiantes/{id}/lista-espera` | Sus esperas: `esperando`, `avisada` (con la `opcion`) o `cancelada` |
| DELETE | `/api/estudiantes/{id}/lista-espera/{espera_id}` | Salir de la lista |

`POST /chat` devuelve además `lista_espera` (`{id, …}`) cuando la persona quedó anotada en ese mensaje. Hoy el aviso es solo dentro del campus; no hay mensajería externa (WhatsApp u otra).

**Aviso proactivo** (la tarjeta «un espacio para ti» del Inicio). Cuatro señales de 1 punto; mínimo **3** y solo en semana de evaluaciones (D7): S1 temporada de evaluación, S2 caída de asistencia ≥ 0,05, S3 caída de nota ≤ −0,5, S4 créditos en el cuartil superior. Sin alerta de abandono (viene de un dato sintético). Se calcula con los datos académicos simulados; la tarjeta se justifica por contexto y la persona puede darla de baja (se recuerda en RAM hasta reiniciar la demo).

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/estudiantes/{id}/aviso-proactivo` | `{mostrar, elegible, descartado, puntaje, minimo, senales[], semana}` |
| POST / DELETE | `/api/estudiantes/{id}/aviso-proactivo/baja` | Darlo de baja / reactivarlo |

En la demo, Lucía cumple S1–S4 (4 puntos) y Diego S1, S2 y S4 (3); Mateo y Valentina solo S1.

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

Con `iniciar.bat` (raíz del repo) todo esto se hace solo: instala `requirements-agente.txt`, inicia Ollama si no está abierto, avisa si falta el modelo y muestra el estado del agente al arrancar.

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
| `AURA_LINEA_AYUDA` | vacío | Línea de ayuda propia de la red, que se nombra en el mensaje de crisis. Vacío: «la línea de ayuda de tu institución» |
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


## Modo lote y avisos en vivo

Con la utilización ≥ 75 %, un servicio entra en modo lote y `proponer_opciones` ya no ofrece sus cupos (ver [como_funciona.md §8](como_funciona.md)). Si lo único compatible está ahí, la respuesta trae `lote_oferta`; al aceptar, el agente llama a `entrar_a_lote` y la respuesta trae `lote`. Cuando el lote se cierra solo, la persona recibe su cita **sin enviar ningún mensaje**:

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/estudiantes/{estudiante_id}/avisos?desde=` | Avisos de la persona con id mayor que `desde` → `{epoca, ultimo_id, avisos[]}` |
| GET | `/api/estudiantes/{estudiante_id}/avisos/stream?desde=` | Lo mismo en tiempo real (SSE, `event: aviso`; mismo formato que el flujo de actividad: `inicio`, `reinicio`, `: ping`) |
| POST | `/api/appointments/lote` | Entrar al lote por API (cuerpo como `proposals`); solo vale si `proposals` devolvió `motivo_vacio: "servicios_en_lote"`. `409 ya_en_lote` si ya espera |

**El servicio que la persona quiere está en lote, pero hay alternativas directas.** Estar en lote no significa que no queden plazas (al 75 % todavía hay 25 % libre): solo que se reparten en conjunto. Si lo directo son únicamente servicios alternativos (p. ej. pares) y el servicio ideal tiene plazas en lote, `POST /proposals` devuelve las opciones **y además** `lote` con `lote_para_ideal: true`; el chat muestra ambas cosas (`opciones` y `lote_oferta`) y el agente le dice que, si prefiere específicamente ese servicio, puede entrar a su lote. Quien entra así queda marcado `solo_servicio_ideal`: el motor no le asigna un servicio alternativo (si no hay plaza de ese servicio, queda como sin cupo y se le avisa). La API admite el mismo campo `solo_servicio_ideal` en las solicitudes.

Cada aviso: `{id, estudiante_id, tipo, registrado_en, ...}` con `tipo` = `lote_en_espera`, `lote_asignada` (trae `mensaje` y `cita`, como `CitaOut`), `lote_sin_cupo` (`mensaje`) o `lote_error`. Además, el texto del resultado se agrega a la conversación (`GET /api/chat/{session_id}` lo devuelve) para que el agente sepa qué pasó.
