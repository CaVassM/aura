# AURA — Backend

API de la plataforma (FastAPI) y motor de asignación. **Todo el estado vive en RAM, en un solo proceso**: al reiniciar se pierden citas y desencuentros nuevos, y la demo se vuelve a sembrar igual (semilla fija). No hay base de datos.

## Dos servicios separados

```text
src/backend/
├── app/                          # PLATAFORMA — capas como en Spring
│   ├── main.py                   #   crea la app, CORS, routers; construye y siembra el AppState (lifespan)
│   ├── deps.py                   #   inyección con Depends()
│   ├── settings.py               #   AURA_DATA_DIR, AURA_CORS_ORIGINS
│   ├── api/                      #   routers: reciben y devuelven, sin lógica
│   ├── schemas/                  #   modelos Pydantic de entrada y salida (response_model)
│   ├── services/                 #   lógica de negocio (resumen, servicios, desencuentros, reglas, citas, siembra…)
│   ├── repositories/             #   AppState en memoria (singleton + lock), citas, lectura de D6
│   ├── models/                   #   entidades (Cita)
│   └── cli_siembra.py            #   resumen por consola de la siembra
│
├── agente/                       # AGENTE CONVERSACIONAL — LangChain + Ollama (gemma4)
├── aura/                         # MOTOR DE ASIGNACIÓN — servicio independiente
│   ├── servicio.py               #   ÚNICA puerta de entrada: ServicioAsignacion
│   ├── motor/  herramientas/  aviso/  datos/
│
├── config/  data_pack/  docs/  experimentos/  salidas/  tests/
```

Regla de dependencia: `app/` usa el motor solo a través de `aura.servicio.ServicioAsignacion` (y de los tipos de `aura.datos`); `aura/` no importa nada de `app/` ni de `experimentos/`. El agente conversacional (`agente/`, LangChain + Ollama) no importa `app/` ni `aura/`: usa el puerto `agente/puerto.py`, que implementa la plataforma ([API del agente](docs/api_agente.md)). Las herramientas del motor están en [contrato](docs/contrato_herramientas.md).

## Cómo funciona la demo

Al arrancar se construye un `AppState` único (D6, YAML, agenda, citas, desencuentros) y se **siembra la demanda de una semana simulada** con el motor en modo directo (orden de llegada, mejores opciones con k=1):

- demanda base: semana mediana de D2 (sin D1), escalada por el escenario (`demo.escenario`, por defecto `x6`; `x1` y `x4.3` siguen disponibles);
- más solicitudes de «vespertino que trabaja» (19:00–21:00) en la proporción `demo.proporcion_vespertino_trabaja` (**10 %, supuesto de simulación**; el valor observado en D5 es 55/2500 = 2,2 %);
- las solicitudes sin opción compatible quedan como desencuentros, registrados por el motor;
- todo es determinista con `demo.semilla`. Si falta D2, el arranque falla con un mensaje claro.

Fechas: los pedidos simulados se fechan dentro de la semana de evaluaciones de D7 (lunes 2026-11-09 a domingo 11-15, con el día de la semana que trae D2) y `demo.hoy` es el domingo **2026-11-15**: todo lo sembrado queda en el pasado o en hoy. Cada pedido se procesa en orden de llegada y solo ve cupos de su fecha + 1 a su fecha + 14 días; los pedidos en vivo usan `hoy`. La agenda va del 11-10 al 11-29 (la capacidad de D6 se reparte por semana Lun–Dom, proporcional en la semana cortada) y la **agenda abierta** (lo reservable) del 11-16 al 11-29. Cupos liberados y ocupación se miden solo sobre la agenda abierta; citas, espera media y desencuentros cuentan todo lo sembrado. La espera es `fecha_cupo − fecha_solicitud`, como `wait_days` en D2. Definiciones completas en [docs/api_coordinacion.md](docs/api_coordinacion.md).

## Instalar y correr

Desde `src/backend`, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Swagger en `http://localhost:8080/docs`. El arranque tarda unos segundos (construye la agenda y siembra la demo). Con `--reload`, cada recarga reinicia el estado.

### Variables de entorno

| Variable | Para qué | Por defecto |
|---|---|---|
| `AURA_DATA_DIR` | Carpeta del Data Pack (D2 y D6 son obligatorios para la demo; D3 para aviso) | `data_pack_path` de `config/parametros.yaml` (`data_pack/`) |
| `AURA_CORS_ORIGINS` | Orígenes extra permitidos, separados por coma | siempre `http://localhost:3000` y `http://localhost:5173` |
| `AURA_D5_PATH` | `D5_help_line_conversations.json` (solo `experimentos.comparar_d5`) | `d5_path` del YAML |

```powershell
$env:AURA_DATA_DIR = "ruta\DataPack_Aethera_Oleada1"
```

El Data Pack no se copia al repo salvo D1, D2, D6 y D7 en `data_pack/`; las respuestas de la API nunca devuelven filas crudas.

## Endpoints (prefijo `/api`)

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/salud` | `{"ok": true}` |
| GET | `/demo/estado` | Fecha demo, semana, horizonte y etiqueta del escenario |
| POST | `/demo/reiniciar` | Reconstruye el estado y vuelve a sembrar |
| GET | `/coordinacion/resumen?semana=` | KPI y ocupación por servicio |
| GET | `/coordinacion/servicios?tipo=&canal=&solo_alta_demanda=&semana=` | GeoJSON para el mapa |
| GET | `/coordinacion/servicios/{service_id}?semana=` | Detalle: cupos por día y desencuentros recientes |
| GET | `/coordinacion/desencuentros?motivo=&distrito=&servicio_ideal=&grupo=&pagina=&tamano=` | Tabla, heatmap e insight |
| GET | `/coordinacion/desencuentros.csv` | Los mismos filtros, sin paginar |
| GET | `/coordinacion/reglas` | Reglas del motor (solo lectura, con `provisional`) |
| GET | `/services`, `/services/{id}/slots` | Catálogo y cupos libres (estudiante) |
| POST | `/appointments/proposals?k=` | Opciones compatibles, sin reservar (estudiante) |
| POST / GET / DELETE | `/appointments`, `/appointments?estudiante_id=`, `/appointments/{id}` | Reservar, listar y cancelar (estudiante) |
| POST | `/chat` | Mensaje al agente conversacional (requiere Ollama) |
| GET / DELETE | `/chat/{session_id}?estudiante_id=` | Releer o borrar una conversación |
| GET | `/chat/estado` | Diagnóstico de Ollama y del modelo |

Contrato con ejemplos JSON: [docs/api_coordinacion.md](docs/api_coordinacion.md). Contrato del chat y cómo instalar el agente: [docs/api_agente.md](docs/api_agente.md) (`pip install -r requirements-agente.txt`; sin eso, `/api/chat` responde 503 y el resto funciona).

## Parámetros de la demo (`config/parametros.yaml`)

`demo.hoy`, `demo.escenario` (`x1`, `x2`, `x4.3`, … de `experimento.escenarios`), `demo.semilla`, `demo.proporcion_vespertino_trabaja`, `demo.etiqueta_*`, `demo.espera_linea_base_dias` (si D2 no está) y `coordinacion.*` (umbrales de nivel, heatmap). Etiquetas en español y marcas de provisional en `config/tablas.yaml` (`etiquetas`, `provisional`).

## Pruebas y comandos

```powershell
python -m pytest -q                    # motor, herramientas, aviso, API y siembra
python -m app.cli_siembra x1 x4.3     # resumen de la siembra por escenario
python -m app.cli_chat                # conversar con el agente en la terminal (requiere Ollama)
python -m experimentos.demo_herramientas
python -m experimentos.validar_aviso   # requiere D3 (AURA_DATA_DIR)
python -m experimentos.experimento_genetico
python -m experimentos.comparar_d5     # requiere D3 y D5
```

`salidas/` conserva solo reportes `.md` y gráficos `.png`; los CSV y JSON de los experimentos no se versionan.

## Documentación

- [API de Coordinación (contrato para el front)](docs/api_coordinacion.md)
- [Cómo funciona AURA](docs/como_funciona.md)
- [API del agente conversacional (endpoints, parámetros, instalación con Ollama)](docs/api_agente.md)
- [Contrato de herramientas del agente](docs/contrato_herramientas.md)
- [Resultados clave para el concurso](docs/resultados_clave.md)
- [Decisiones pendientes del equipo](docs/decisiones_pendientes.md)
- [Reporte de comparación D5 vs AURA](salidas/reporte_comparacion_d5.md)
