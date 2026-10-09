# AURA

AURA es un prototipo que propone y asigna citas para servicios de apoyo estudiantil.
Combina reglas de disponibilidad, un optimizador y herramientas que puede llamar un agente conversacional.
Sus resultados son apoyo operativo: no diagnostica ni reemplaza una decisión humana.

## Cómo correrlo

En Windows, desde esta carpeta, doble clic en `iniciar.bat` (o `.\iniciar.bat` en la terminal). Prepara el entorno de Python (backend **y** agente conversacional: LangChain + langchain-ollama) y las dependencias de Node si faltan, comprueba Ollama (lo inicia si no está abierto y avisa si falta el modelo), levanta el backend (http://localhost:8080) y el frontend (http://localhost:3000) y abre el panel de Coordinación; el chat del estudiante queda en http://localhost:3000/campus/chat. `Ctrl+C` detiene los servidores (y Ollama, si lo inició el script); `.\iniciar.bat -Detener` cierra lo que haya quedado en los puertos 8080 y 3000. Requiere Python 3.10+, Node 18+ y [Ollama](https://ollama.com) con el modelo descargado (`ollama pull gemma4`, o el que pongas en `AURA_OLLAMA_MODEL` en `src\backend\.env`; ver [docs/api_agente.md](src/backend/docs/api_agente.md)). El agente corre dentro del backend: no hay otro proceso que levantar. Sin Ollama, todo funciona salvo el chat. Los logs quedan en `logs/`.

## Árbol del proyecto

```text
aura/
└── src/
    ├── frontend/             # interfaz Next.js (Entregable 2)
    └── backend/              # API de plataforma (MVC) + motor de asignación, todo en RAM
        ├── app/              #   plataforma (api, schemas, services, repositories, models)
        ├── agente/           #   agente conversacional (LangChain + Ollama)
        ├── aura/             #   motor: algoritmo genético, herramientas del agente, filtros de aviso
        ├── config/           #   parámetros y tablas editables
        ├── data_pack/        #   D1, D2, D6 y D7
        ├── docs/             #   explicación, contrato y decisiones del equipo
        ├── experimentos/     #   escenarios, demo, validaciones y comparación con D5
        ├── salidas/          #   reportes y gráficos
        └── tests/            #   pruebas del motor, herramientas, filtros y API
```

- Backend (arquitectura, endpoints, variables de entorno y comandos): [src/backend/README.md](src/backend/README.md)
- Contrato de la API de Coordinación: [src/backend/docs/api_coordinacion.md](src/backend/docs/api_coordinacion.md)
- Frontend: [src/frontend/README.md](src/frontend/README.md)
- Cómo funciona el motor: [src/backend/docs/como_funciona.md](src/backend/docs/como_funciona.md)
- Agente conversacional (endpoints, parámetros, instalación con Ollama): [src/backend/docs/api_agente.md](src/backend/docs/api_agente.md)
- Contrato de herramientas del agente: [src/backend/docs/contrato_herramientas.md](src/backend/docs/contrato_herramientas.md)
- Resultados clave para el concurso: [src/backend/docs/resultados_clave.md](src/backend/docs/resultados_clave.md)
- Decisiones pendientes del equipo: [src/backend/docs/decisiones_pendientes.md](src/backend/docs/decisiones_pendientes.md)
