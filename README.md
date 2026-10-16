# AURA — Paralelo Sur

**Misión M6: Barreras de Acceso** · Desafío Ciudad Aethera 2026.

**Integrante registrado en el repositorio:** CaVassM. Añade aquí los demás integrantes del equipo, si corresponde.

AURA ayuda a estudiantes a encontrar y reservar citas de apoyo compatibles con sus horarios, canales y distrito. Cuando un servicio supera el 75 % de utilización, agrupa solicitudes compatibles y reparte los cupos con un algoritmo genético. El panel permite a Coordinación seguir la demanda, los desencuentros y las asignaciones.

## Cómo funciona

El campus Next.js conversa con un agente Qwen 3.5 4B que usa herramientas para consultar y reservar la agenda. La API FastAPI aplica las reglas de afinidad, disponibilidad y equidad; el motor propone citas y usa un algoritmo genético para resolver lotes. El panel de Coordinación consume la misma API. El estado de la demo vive en RAM.

El agente usa `qwen3.5:4b`, un modelo de pesos abiertos que corre localmente con Ollama; no requiere servicios de IA pagados. La técnica combina tool calling, un motor de reglas y optimización genética en modo lote.

## Datos

- **D2:** demanda y esperas observadas; alimenta el escenario simulado y la línea base de espera.
- **D3:** trayectorias académicas para validar de forma agregada las señales del aviso.
- **D5:** conversaciones de referencia para analizar derivaciones; no se usa para identificar estudiantes.
- **D6:** catálogo, servicios, capacidad, horarios y distritos.
- **D7:** calendario académico y semanas de evaluación.
- **D1:** solo se usa para comparar promedios de ansiedad entre grupos elegibles y no elegibles; nunca para seleccionar personas.

El Data Pack es material del desafío y **no se redistribuye** con este repositorio. Los datos de D1–D7 deben obtenerse por separado y configurarse mediante `AURA_DATA_DIR` o `src/backend/data_pack/`.

## Video

[ENLACE_VIDEO]

## Ejecutar con Docker Compose

Requisitos: Docker Desktop y el Data Pack. Para usar el agente también se requiere Ollama en el equipo con `qwen3.5:4b` descargado.

1. Copia `.env.example` a `.env`, configura `AURA_CORS_ORIGINS` y, si vas a publicar la API, el token del túnel con nombre.
2. Coloca el Data Pack en `src/backend/data_pack/` o configura `AURA_DATA_HOST_DIR`.
3. Inicia el backend: `docker compose up -d --build`.
4. Para el túnel con nombre: `docker compose --profile tunnel up -d --build`. Configura el hostname en Cloudflare para que apunte a `http://backend:8080`.
5. El frontend se ejecuta desde `src/frontend` con `npm ci && npm run dev`, o se despliega en Vercel con `NEXT_PUBLIC_API_URL` apuntando al backend.

El túnel rápido de Cloudflare es temporal y su URL cambia al reiniciarlo; no es un despliegue permanente. Consulta [DESPLIEGUE.md](DESPLIEGUE.md), [backend](src/backend/README.md) y [frontend](src/frontend/README.md) para los pasos completos.

## Estructura

```text
src/
├── frontend/   Campus y panel de Coordinación (Next.js)
└── backend/    API FastAPI, agente, motor, reglas, datos y documentación
```

El escenario de demo actual usa demanda ×6, 10 % de estudiantes vespertinos que trabajan y `hoy = 2026-11-15`. La espera se calcula como `fecha_cupo − fecha_solicitud`, igual que en D2. Resultados y supuestos se documentan en [resultados clave](src/backend/docs/resultados_clave.md) y [cómo funciona](src/backend/docs/como_funciona.md).
