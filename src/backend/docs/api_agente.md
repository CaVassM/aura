# API del agente conversacional (estudiante)

El agente AURA conversa con la persona, entiende el motivo, reúne sus preferencias y usa las herramientas de la agenda para **proponer, reservar y cancelar citas**. Funciona con **LangChain + Ollama** con un modelo local de pesos abiertos (por defecto **Qwen 3.5 4B**, `qwen3.5:4b`; sin servicios pagados). Todo el estado (conversaciones y citas) vive en RAM, igual que el resto del backend.

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
| `opciones` | lista | Si el agente **acaba de proponer** citas: **como máximo 3** tarjetas para mostrar (mismos campos que `OpcionOut` de `POST /appointments/proposals`; un servicio en modo lote es una opción con `tipo_opcion: "lote"`, sin día ni hora). **No hay nada reservado todavía**: la persona elige escribiendo, o el portal envía «quiero la opción 2» como mensaje al tocar una tarjeta (la numeración es el orden de la lista `opciones`, desde 1) |
| `cita` | objeto \| null | Cita reservada en este mensaje (mismo formato que `CitaOut` de `/appointments`: `id`, `servicio_nombre`, `tipo`, `tipo_label`, `distrito`, `hora_fin`, `slot.fecha_iso`, `canal`, `estado`) |
| `cita_cancelada` | objeto \| null | Cita cancelada en este mensaje |
| `desencuentro_registrado` | bool | El agente avisó al equipo que no había opción compatible |
| `mensaje` | string \| null | Texto que redactó el backend para la última búsqueda en los casos especiales (sin cupos, servicio en lote, servicio pedido por nombre sin cupo): el agente lo muestra tal cual |
| `ya_tiene_cita` | objeto \| null | R7: ya tiene una cita activa de ese tipo de servicio. `{cita, mensaje}`; el `mensaje` termina en «¿Quieres cambiarla por esta?». Si la persona confirma, el agente vuelve a reservar con `reemplazar` y la anterior se cancela en la misma operación |
| `lote` | objeto \| null | Eligió una **opción por lote**: su solicitud quedó pendiente en el lote y el resultado llega después al mismo chat. `{id, estado: "en_espera", posicion, solicitudes, tamano_maximo, cierra_en}`. La cita queda en `null` `{id, estado: "en_espera", posicion, solicitudes, tamano_maximo, cierra_en}`. `cierra_en` (ISO UTC) sirve para la cuenta regresiva; el lote se cierra solo |
| `alerta_crisis` | bool | El mensaje activó el protocolo de ayuda inmediata (la respuesta es un texto fijo que remite a emergencias y a la línea de ayuda de la institución; no se llamó al modelo) |
| `herramientas_usadas` | lista | `[{"nombre": "proponer_opciones", "ok": true}, …]`, en orden. Útil para depurar |

```json
{
  "session_id": "5f0c1d…",
  "respuesta": "Entiendo, los parciales pesan. Encontré estas opciones para el miércoles por la tarde: …",
  "opciones": [{
    "opcion_id": "C0000321|digital", "tipo_opcion": "cupo", "service_id": "SRV_AE_001", "servicio_nombre": "Espacio Brújula Orientación",
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
{"modelo": "qwen3.5:4b", "url": "http://localhost:11434", "dependencias_instaladas": true,
 "ollama_disponible": true, "modelo_instalado": true, "detalle": "Listo."}
```

## Herramientas que usa el agente

El modelo las llama solo; no son endpoints. Están en `agente/herramientas.py` y llegan a la agenda a través de `CitasService` (igual que la API de citas).

| Herramienta | Parámetros que elige el modelo | Qué hace |
|---|---|---|
| `proponer_opciones` | `motivo`, `franjas` [{`dia` Mon–Sun, `desde`, `hasta` HH:MM}], `canales_aceptables` (`digital`, `phone`, `in_person`), `distrito`\*, `grupo`\*, `fecha` (AAAA-MM-DD, solo si la persona pidió una fecha concreta), `service_id_preferido` (solo si la persona nombró un servicio, p. ej. «Brújula»), `k` (1–5; se recorta a **3**) | Busca **como máximo 3** citas compatibles, una por servicio/fecha/hora/canal: primero las del servicio pedido por nombre o, si no pidió ninguno, las del servicio ideal; las alternativas afines solo completan. Un servicio en modo lote sale como **una opción de tipo `lote`** («Asignación en grupo»). Con `fecha` solo trae ese día; si no hay cupos ese día, trae las fechas más cercanas. Devuelve `mensaje` (texto del backend para los casos especiales, que el modelo muestra tal cual). Si no hay ningún cupo compatible, **la herramienta registra el desencuentro** (a lo más uno por servicio ideal y franja dentro de la conversación). No reserva. Repetir la misma búsqueda en un mensaje devuelve `busqueda_repetida` |
| `reservar_cita` | `numero` (1, 2, 3… de la última lista), `reemplazar` (solo tras confirmar el cambio) | Reserva esa opción: un cupo (queda la cita, con la línea del canal: enlace por correo en videollamada, llamada al número registrado en teléfono, o el lugar en presencial) o, si es de tipo `lote`, deja la solicitud **pendiente** en el lote. **R7:** si ya tiene una cita activa de ese tipo de servicio responde `ya_tiene_cita` con el mensaje «Ya tienes una cita de … el … a las …. ¿Quieres cambiarla por esta?»; con `reemplazar` (y solo si la persona confirmó) se cancela la anterior y se reserva la nueva en una sola operación. El modelo nunca ve ni copia identificadores internos |
| `cancelar_cita` | `cita_id` | Cancela una cita **de esa persona** |
| `listar_mis_citas` | — | Lista las citas de la persona |
| `consultar_asistencia` | — | Lee la **asistencia a clases** de la persona (período actual, anterior y por curso). Es el **único** dato académico que ve el agente; se niega (`no_pidio_asistencia`) si la persona no habló de su asistencia o sus faltas |
| `avisarme_si_hay_cupo` | — | Anota a la persona en la **lista de espera** con su última búsqueda. Solo cuando no hubo opciones **y** la persona aceptó que le avise (mismo bloqueo `falta_confirmacion`) |
| `registrar_desencuentro` | — | Avisa que no hubo opción: guarda la última búsqueda. Normalmente ya queda registrado solo cuando `proponer_opciones` no devuelve opciones, así que no se duplica; si hay cupos compatibles (normales o en lote) la plataforma lo rechaza (`hay_cupos_compatibles`): un desencuentro es que no exista ninguno |

`proponer_opciones` se **niega a buscar** (`faltan_datos`) si en la conversación la persona no ha mencionado días ni canal (`agente/entrada.py`; basta una mención, incluso «cualquier día» o «da igual»). Es una red de seguridad contra modelos pequeños que inventan esos datos; el agente debe preguntárselos (tolera letras repetidas por error de tipeo). Del mismo modo, `cancelar_cita` se niega (`falta_confirmacion`) si el mensaje no pide cancelar ni responde «sí» a una pregunta de cancelar. Cada opción llega al modelo con un `texto` ya redactado (servicio, día, fecha, hora y canal) para que lo copie.

\* Opcionales si ya se enviaron en `POST /chat`. Si no hay distrito, el agente lo pregunta.

`estudiante_id` **no** es parámetro de ninguna herramienta: sale de la sesión. Motivos válidos: `academic_pressure`, `sleep_and_routine`, `social_support`, `career_concern`, `preventive_guidance`, `service_navigation` (su servicio ideal está en `config/tablas.yaml`).

### Guardrails y respaldo (antes y alrededor del modelo)

Las reglas viven en las herramientas y en el backend, no en el prompt: el modelo solo conversa y muestra lo que devuelven las herramientas. Antes de invocarlo corre una capa **determinística** (`agente/crisis.py`, `agente/guardrails.py`) que responde con texto fijo sin llamar al modelo:

| Guardrail | Cuándo | Respuesta |
|---|---|---|
| Crisis (riesgo inmediato) | Frases de autolesión o suicidio («no quiero vivir»…) | Tarjeta de ayuda inmediata (`alerta_crisis: true`) |
| Límite clínico | Piden un medicamento o un diagnóstico («¿qué medicamento debería tomar?», «creo que tengo depresión») | «No puedo diagnosticar ni recomendar medicamentos; eso lo ve un profesional. Si quieres, te ayudo a agendar con consejería.» No es una crisis y el flujo normal sigue en el siguiente mensaje. Si el mensaje ya pide una cita, lo atiende el modelo |
| Datos de profesionales | Piden el número o el contacto de un psicólogo, psiquiatra, etc. | Explica que solo muestra los servicios de la red de bienestar y ofrece agendar |

**Respaldo ante llamadas mal formadas.** Si el modelo emite una llamada a herramienta mal formada (error del modelo, o la escribe como texto en vez de hacerla), el agente **reintenta una vez**; si vuelve a fallar responde un mensaje seguro («No logré terminar eso. ¿Me lo cuentas de nuevo…?») y el chat no se rompe. Si en ese turno ya se reservó, canceló o registró algo, no se reintenta (no se duplica una acción).

### Asistencia: lo único académico que ve el agente

`consultar_asistencia` devuelve solo `periodo`, `asistencia_actual`, `asistencia_periodo_anterior`, `variacion`, `minimo_requerido` y, por curso, `curso`, `asistencia`, `faltas`, `de_sesiones` y `bajo_el_minimo`. **No** hay notas, créditos, docentes, alertas ni encuesta D1 (la regla ya documentada en [como_funciona.md §2](como_funciona.md): D1 no se entrega al agente; de lo académico, solo la asistencia, que es la señal S1 del aviso). Para el agente no es un diagnóstico: el prompt le pide contar las cifras en simple, no hablar de riesgo ni de avisos, y ofrecer una cita de bienestar si le preocupa. Está implementado en `AcademicoService.asistencia_para_agente` y `PuertoPlataforma.asistencia`; los datos son simulados (ver abajo) y solo existen para los perfiles de la demo (`STU_DEMO_001…004`): para otra persona devuelve `sin_datos_academicos`.

## Vida académica del campus (cursos, calificaciones, calendario)

Alimentan las páginas `Mis cursos`, `Calificaciones` y `Calendario` del campus. **Simulado** (ni D1 ni D7 traen cursos, horarios ni notas): se inventa para los cuatro perfiles de la demo en `app/repositories/academico_repository.py`. Lo único real es el **calendario D7**: período `PER_2026_4` (5 oct – 23 dic), semanas de evaluación y actividades, filtrados por la institución y el distrito de la persona (`ALL` o el suyo: la pausa de bienestar es solo de Gaia; el encuentro estudiantil, solo de su institución y distrito). Estos endpoints son de lectura y los usa el frontend, no el agente.

| Método | Ruta | Devuelve |
|---|---|---|
| GET | `/api/estudiantes/{id}/academico/cursos` | `periodo` (semana, avance, evaluación en curso/próxima), `asistencia` (tasa, anterior, variación), `cursos[]` (horario, docente, aula, asistencia, promedio parcial, próxima evaluación) |
| GET | `/api/estudiantes/{id}/academico/calificaciones` | `escala` (1,0–7,0; aprueba 4,0), `promedio_general` y `variacion` (vs. período anterior), `cursos[]` con `evaluaciones[]` (nota, peso, estado `calificada`/`sin_publicar`/`programada`), `nota_necesaria` y `situacion` |
| GET | `/api/estudiantes/{id}/academico/calendario` | `eventos[]`: eventos D7 (`periodo_inicio`, `periodo_fin`, `semana_evaluacion`, `bienestar`, `actividad_universitaria`), `clase` (con `estado` `asistio`/`falto`/`programada`) y `evaluacion` |

`404 no_encontrado` si la persona no es un perfil de la demo. «Hoy» es el de la demo (`GET /api/demo/estado`, 15 nov 2026, último día de las evaluaciones intermedias).

Supuestos de la simulación (no salen de los datos): sin clases en las semanas de evaluación de D7; los exámenes parciales y finales caen dentro de esas semanas; asistencia mínima de **70 %**; escala 1,0–7,0 como `average_grade` de D3 y aprobación en 4,0; las inasistencias y notas son inventadas (Lucía y Diego tienen caída de asistencia frente al período anterior, para ilustrar la señal S1; Mateo y Valentina no).

## Lista de espera y aviso proactivo

**Lista de espera.** Si no hay ningún cupo compatible, la herramienta registra el desencuentro y el agente pregunta si quiere que le avise; si dice que sí, queda anotada. Cada vez que se **cancela una cita** (lo único que libera cupos) se revisa la lista en orden de llegada: a quien le sirva un cupo libre (sin contar servicios en modo lote) le llega un aviso `cupo_disponible` por `/avisos/stream` con la opción lista para tocar, y la opción queda como «opción 1» de su conversación. No retiene el cupo: avisa y la persona decide; un mismo cupo se avisa a una sola persona. En Coordinación aparece en *En vivo* (`lista_espera_alta` y `lista_espera_aviso`).

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/api/appointments/lista-espera` | Anotarse por API (cuerpo como `proposals`); repetir la misma no la duplica |
| GET | `/api/estudiantes/{id}/lista-espera` | Sus esperas: `esperando`, `avisada` (con la `opcion`) o `cancelada` |
| DELETE | `/api/estudiantes/{id}/lista-espera/{espera_id}` | Salir de la lista |

`POST /chat` devuelve además `lista_espera` (`{id, …}`) cuando la persona quedó anotada en ese mensaje. Hoy el aviso es solo dentro del campus; no hay mensajería externa (WhatsApp u otra).

**Aviso proactivo** (la tarjeta «un espacio para ti» del Inicio). En semana de evaluaciones de D7, aparece con al menos **2 de estas 3 señales**: caída de asistencia ≥ 0,05, baja de nota ≤ −0,5 y carga de créditos en el cuartil superior. La semana de evaluaciones es la condición, no una señal; no se usa `dropout_alert`. Se calcula con los datos académicos simulados y la persona puede darlo de baja (se recuerda en RAM hasta reiniciar la demo).

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/estudiantes/{id}/aviso-proactivo` | `{mostrar, elegible, descartado, puntaje, minimo, senales[], semana}` |
| POST / DELETE | `/api/estudiantes/{id}/aviso-proactivo/baja` | Darlo de baja / reactivarlo |

**Regla del aviso:** en semana de evaluaciones (D7), aparece con al menos 2 de 3 señales (S1 caída de asistencia, S2 baja de nota, S3 carga de créditos alta); la semana de evaluaciones es la condición, no una señal. En la demo, Lucía cumple las 3 y Diego 2 (S1 y S3); Mateo y Valentina ninguna. Ver [como_funciona.md §2](como_funciona.md).

## Instalar y probar en tu PC

Requisitos: Python 3.12+ y `uv` (`pip install uv`, una vez), [Ollama](https://ollama.com) con el modelo descargado (`ollama pull qwen3.5:4b`; usa el nombre exacto de `ollama list`) y una versión reciente de Ollama (el modelo debe admitir herramientas).

```powershell
# desde src/backend: crea .venv e instala exactamente lo de uv.lock (app + agente)
uv sync --extra agente
Copy-Item .env.example .env                   # opcional: cambia AURA_OLLAMA_MODEL si tu modelo se llama distinto

ollama serve                                  # si Ollama no está abierto ya
uv run uvicorn app.main:app --reload --port 8080   # Swagger: http://localhost:8080/docs
```

Con `iniciar.bat` (raíz del repo) todo esto se hace solo: instala el extra `agente` (`uv sync --extra agente`), inicia Ollama si no está abierto, avisa si falta el modelo y muestra el estado del agente al arrancar.

Sin frontend, desde la terminal: `python -m app.cli_chat --distrito DIST_GAIA` (muestra también qué herramientas llamó el modelo).

Si el backend arranca sin el extra `agente`, todo funciona excepto `/api/chat`, que responde `503` con el comando de instalación.

### Variables de entorno (todas opcionales)

| Variable | Por defecto | Para qué |
|---|---|---|
| `AURA_OLLAMA_MODEL` | `qwen3.5:4b` | Nombre del modelo en Ollama |
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
- Seguridad: crisis (`agente/crisis.py`) y los guardrails de límite clínico y datos de profesionales (`agente/guardrails.py`) responden con texto fijo sin llamar al modelo; el prompt prohíbe diagnosticar; las herramientas no dejan reservar ids inventados ni cancelar citas ajenas, y aplican las reglas (máximo 3 opciones, R7, desencuentro solo sin cupos).
- Pruebas (no necesitan Ollama): `python -m pytest tests/test_agente_chat.py tests/test_agente_ollama_http.py tests/test_validacion_herramientas.py`. Usan un modelo guionado y un servidor que imita la API HTTP de Ollama; **no validan la calidad de las respuestas del modelo**, eso se prueba conversando (`python -m app.cli_chat`).


## Modo lote y avisos en vivo

Con la utilización ≥ **75 %** (`modo_lote_umbral_utilizacion: 0.75`, un solo valor en el YAML que también define el nivel «alta» del panel), un servicio entra en modo lote y sus cupos dejan de ofrecerse uno a uno (ver [como_funciona.md §8](como_funciona.md)). **No se oculta**: `proponer_opciones` lo devuelve como **una sola opción** `tipo_opcion: "lote"` (en la interfaz, «Asignación en grupo»; `opcion_id` = `LOTE|<service_id>`, con `servicio_nombre`, `tipo`, `cupos_libres`, `tiempo_respuesta_s` y un `mensaje` listo para mostrar: «Este servicio tiene mucha demanda; sus cupos se reparten en grupo. Te confirmo en unos segundos.»), ordenada con el costo de su mejor cupo como cualquier otra. Al elegirla (`reservar_cita`) la solicitud queda **pendiente** en el lote (la respuesta trae `lote`) y, cuando el lote se cierra solo, la persona recibe su cita **sin enviar ningún mensaje**. **Entrar a un lote nunca registra un desencuentro**: solo lo es no tener ningún cupo compatible, ni normal ni en lote (si al resolverse el lote ya no queda ninguno, ahí sí; si quedan, se le ofrecen esas opciones en el mismo chat). Para ver el aviso y la cita la persona no tiene que escribir:

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/api/appointments/lote` | Entrar al lote por API (cuerpo como `proposals`); vale si algún servicio compatible está en modo lote. `409 ya_en_lote` si ya espera; `409 ya_tiene_cita` (R7) |

**Máximo 3 opciones y orden.** `proponer_opciones` devuelve como máximo 3 (`max_opciones` en `parametros.yaml`). Primero van las del servicio que la persona pidió por nombre (`service_id_preferido`: un id o un nombre como «Brújula») o, si no pidió ninguno, las del servicio ideal; las alternativas afines solo completan si faltan. Si el servicio pedido no tiene cupos compatibles, la respuesta lo dice (`preferido.disponible: false`, `mensaje`) e incluye su fecha más cercana y, aparte, la mejor opción del mismo tipo en otro servicio. **Toda respuesta trae `mensaje`** (el backend redacta los casos especiales para que el modelo no los invente).

**Equidad (R7).** Máximo 1 cita activa por persona y tipo de servicio dentro del horizonte (`max_citas_activas_por_tipo`). Reservar otra del mismo tipo falla con `409 ya_tiene_cita` y `{cita, mensaje}`; con `reemplazar: true` se cancela la anterior y se reserva la nueva en una sola operación (si el cupo nuevo ya no está, la anterior se conserva).

Cada aviso: `{id, estudiante_id, tipo, registrado_en, ...}` con `tipo` = `lote_en_espera`, `lote_asignada` (trae `mensaje` y `cita`, como `CitaOut`), `lote_sin_cupo` (`mensaje`) o `lote_error`. Además, el texto del resultado se agrega a la conversación (`GET /api/chat/{session_id}` lo devuelve) para que el agente sepa qué pasó.
