# AURA — Paralelo Sur

> Desafío Ciudad Aethera 2026 · Red de Bienestar Estudiantil AETHERA · Entregable 2

## 1. Equipo

- **Nombre del equipo:** Paralelo Sur
- **Integrantes (universidad / carrera):**
  - Gabriela Paz Cardenas Hidalgo – Universidad Peruana de Ciencias Aplicadas/ Ingeniería de Sistemas de Información
  - Carlos Camilo Vasquez Morales– Pontificia Universidad Católica del Perú / [Carrera]
  - Víctor Fernando Blas Gomez– ESAN / [Carrera]
  - Leonardo MartÍn SolÍs Ortiz– Universidad Tecnológica Metropolitana / [Carrera]


## 2. Misión abordada

**M6: Barreras de Acceso.**

## 3. Video demostrativo

 [ENLACE_VIDEO]

## 4. Qué hace la solución

AURA ayuda a estudiantes a encontrar y reservar citas de apoyo compatibles con sus horarios, canales y distrito. Cuando un servicio supera el 75 % de utilización, agrupa solicitudes compatibles y reparte los cupos con un algoritmo genético. El panel permite a Coordinación seguir la demanda, los desencuentros y las asignaciones.

### Cómo funciona

El campus Next.js conversa con un agente Qwen 3.5 4B que usa herramientas para consultar y reservar la agenda. La API FastAPI aplica las reglas de afinidad, disponibilidad y equidad; el motor propone citas y usa un algoritmo genético para resolver lotes. El panel de Coordinación consume la misma API. El estado de la demo vive en RAM.

```text
Estudiante ─► Campus (Next.js) ─► API FastAPI ─► Agente (LangChain + Ollama, Qwen3.5 4B)
                                       │                     │ tool calling
                                       ▼                     ▼
                            Panel de Coordinación    Motor de reglas + algoritmo genético (modo lote)
```

## 5. Modelos y herramientas de IA utilizados

| Componente | Herramienta | Técnica empleada |
|---|---|---|
| Agente conversacional | `qwen3.5:4b` (pesos abiertos), local con **Ollama** | Modelo de lenguaje con *tool calling* mediante **LangChain** |
| Asignación en modo lote | Algoritmo genético propio | Optimización combinatoria multiobjetivo (no es IA generativa) |
| Propuesta de citas | Motor de reglas | Reglas duras de horario, afinidad, canal, distrito, fecha y disponibilidad |

- El modelo corre localmente: ningún dato de estudiantes sale a servicios de terceros y no se requieren servicios de IA pagados.
- El agente solo dispone de un conjunto cerrado de herramientas (`proponer_opciones`, `reservar_cita`, `cancelar_cita`, `consultar_asistencia`). El identificador del estudiante lo inyecta el backend desde la sesión, no el modelo.
- Las expresiones de crisis se atienden con una respuesta pregrabada, sin pasar por el modelo.
- AURA no diagnostica ni reemplaza una decisión humana.

La ficha completa está en [`FICHA_IA_RESPONSABLE.pdf`](FICHA_IA_RESPONSABLE.pdf).

## 6. Datasets del Data Pack utilizados

- **D1:** solo se usa para comparar promedios de ansiedad entre grupos elegibles y no elegibles; nunca para seleccionar personas.
- **D2:** demanda y esperas observadas; alimenta el escenario simulado y la línea base de espera.
- **D3:** trayectorias académicas para validar de forma agregada las señales del aviso.
- **D5:** conversaciones de referencia para analizar derivaciones; no se usa para identificar estudiantes.
- **D6:** catálogo, servicios, capacidad, horarios y distritos.
- **D7:** calendario académico y semanas de evaluación.

> El Data Pack es material del desafío y **no se redistribuye** con este repositorio, y no se incluyen datos reales de personas. Los datos deben obtenerse por separado y configurarse mediante `AURA_DATA_DIR` o `src/backend/data_pack/`.

## 7. Resultados

| Escenario de demanda | Cobertura | Espera media |
|---|---|---|
| Línea base histórica (D2) | n/a | 41,96 días |
| ×1 (demanda actual) | 100,00 % | 1,91 ± 0,08 días |
| ×2 | 100,00 % | 3,22 ± 0,07 días |
| ×6 (escenario de la demo) | 87,67 % | 6,91 ± 0,07 días |

El escenario de demo usa demanda ×6, 10 % de estudiantes vespertinos que trabajan y `hoy = 2026-11-15`. La espera se calcula como `fecha_cupo − fecha_solicitud`, igual que en D2. Detalle y supuestos en [resultados clave](src/backend/docs/resultados_clave.md) y [cómo funciona](src/backend/docs/como_funciona.md).

## 8. Estructura del repositorio

```text
/ (raíz del repositorio)
├── README.md
├── FICHA_IA_RESPONSABLE.pdf
├── docs/                 memoria técnica + ficha de IA responsable
└── src/
    ├── frontend/         Campus y panel de Coordinación (Next.js)
    └── backend/          API FastAPI, agente, motor, reglas y documentación
```

## 9. Ejecutar con Docker Compose

Requisitos: Docker Desktop y el Data Pack. Para usar el agente también se requiere Ollama en el equipo con `qwen3.5:4b` descargado (`ollama pull qwen3.5:4b`).

1. Copia `.env.example` a `.env`, configura `AURA_CORS_ORIGINS` y, si vas a publicar la API, el token del túnel con nombre.
2. Coloca el Data Pack en `src/backend/data_pack/` o configura `AURA_DATA_HOST_DIR`.
3. Inicia el backend: `docker compose up -d --build`.
4. Para el túnel con nombre: `docker compose --profile tunnel up -d --build`. Configura el hostname en Cloudflare para que apunte a `http://backend:8080`.
5. El frontend se ejecuta desde `src/frontend` con `npm ci && npm run dev`, o se despliega en Vercel con `NEXT_PUBLIC_API_URL` apuntando al backend.

El túnel rápido de Cloudflare es temporal y su URL cambia al reiniciarlo; no es un despliegue permanente. Consulta [DESPLIEGUE.md](DESPLIEGUE.md), [backend](src/backend/README.md) y [frontend](src/frontend/README.md) para los pasos completos.

## Aviso

AURA es un prototipo de apoyo operativo. No diagnostica ni reemplaza a los profesionales de bienestar.
