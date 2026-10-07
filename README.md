# AURA

AURA es un prototipo que propone y asigna citas para servicios de apoyo estudiantil.
Combina reglas de disponibilidad, un optimizador y herramientas que puede llamar un agente conversacional.
Sus resultados son apoyo operativo: no diagnostica ni reemplaza una decisión humana.

## Árbol del proyecto

```text
aura/
└── src/
    ├── frontend/             # interfaz Next.js (Entregable 2)
    └── backend/              # API de plataforma (MVC) + motor de asignación, todo en RAM
        ├── app/              #   plataforma (api, schemas, services, repositories, models)
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
- Contrato de herramientas del agente: [src/backend/docs/contrato_herramientas.md](src/backend/docs/contrato_herramientas.md)
- Resultados clave para el concurso: [src/backend/docs/resultados_clave.md](src/backend/docs/resultados_clave.md)
- Decisiones pendientes del equipo: [src/backend/docs/decisiones_pendientes.md](src/backend/docs/decisiones_pendientes.md)
