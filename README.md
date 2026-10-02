# AURA

AURA es un prototipo que propone y asigna citas para servicios de apoyo estudiantil.
Combina reglas de disponibilidad, un optimizador y herramientas que puede llamar un agente conversacional.
Sus resultados son apoyo operativo: no diagnostica ni reemplaza una decisión humana.

## Árbol del proyecto

```text
aura/
├── aura/                 # datos, motor, herramientas y filtros de aviso
├── config/               # parámetros y tablas editables
├── docs/                 # explicación, contrato y decisiones del equipo
├── experimentos/         # escenarios, demo, validaciones y comparación con D5
├── data_pack/            # D1, D2, D6 y D7 (lo necesario para el genético)
├── salidas/              # reportes y gráficos
└── tests/                # pruebas del motor, herramientas y filtros
```

## Datos

La carpeta [data_pack/](data_pack/) incluye solo lo que necesita el algoritmo genético: `D1_wellbeing_survey.csv`, `D2_support_services.csv`, `D6_services_map.geojson` y `D7_calendar.csv` (más `DATA_DICTIONARY.md`). Con eso funciona `python -m experimentos.experimento_genetico` sin configurar nada.

El resto del Data Pack (D3, D4, D5) no está en el repositorio. Lo necesitan `experimentos.validar_aviso`, `experimentos.comparar_d5`, `experimentos.demo_herramientas` y los tests de herramientas y aviso. Para usarlo, apunta AURA a tu copia completa:

- `AURA_DATA_DIR`: carpeta del Data Pack completo (D1, D2, D3, D6, D7). Si no se define, se usa `data_pack_path` de [config/parametros.yaml](config/parametros.yaml).
- `AURA_D5_PATH`: archivo `D5_help_line_conversations.json` (solo lo usa `experimentos.comparar_d5`).

```powershell
$env:AURA_DATA_DIR = "ruta\DataPack_Aethera_Oleada1"
$env:AURA_D5_PATH  = "ruta\D5_help_line_conversations.json"
```

Requiere Python 3 con `pyyaml`, `numpy` y `matplotlib` (este último solo para los gráficos).

`salidas/` conserva solo reportes `.md` y gráficos `.png`. Los CSV y JSON que producen los experimentos no se versionan; se regeneran con los comandos de abajo.

## Comandos

Desde esta carpeta, en PowerShell:

```powershell
python -m unittest discover -s tests -v
python -m experimentos.demo_herramientas
python -m experimentos.validar_aviso
python -m experimentos.experimento_genetico
python -m experimentos.comparar_d5
```

## Documentación

- [Cómo funciona AURA](docs/como_funciona.md)
- [Contrato de herramientas](docs/contrato_herramientas.md)
- [Resultados clave para el concurso](docs/resultados_clave.md)
- [Decisiones pendientes del equipo](docs/decisiones_pendientes.md)
- [Reporte de comparación D5 vs AURA](salidas/reporte_comparacion_d5.md)
