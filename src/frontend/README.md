# AURA — Frontend (Entregable 2)

Landing → campus virtual del estudiante → chat con AURA → panel de coordinación de la red. **Todo
usa el backend real** (`src/backend`, FastAPI) a través de `lib/api.ts`:

- **Coordinación** (`/coordinacion`): contrato en `src/backend/docs/api_coordinacion.md`.
- **Estudiante** (`/campus/chat`, `/campus/citas`, y `/campus/cursos|calificaciones|calendario` con datos académicos simulados + calendario D7): el chat habla con el agente conversacional
  (LangChain + Ollama) y las citas son las del backend. Contrato en `src/backend/docs/api_agente.md`.
  Hace falta el backend corriendo y `ollama serve` con el modelo descargado; si el backend no responde,
  las pantallas muestran un mensaje claro y la conversación explica qué falta.

> **Todo vive en RAM en el backend.** Si se reinicia (o se pulsa «Reiniciar demo» en Coordinación) se
> pierden citas y conversaciones; el chat lo detecta y empieza una conversación nueva sin romperse.

## 1. Instalar y correr

```bash
cd aura-frontend
npm install
npm run dev
```

Abre `http://localhost:3000`. Ese es el landing (tu captura 1). Desde ahí:
- "Ingresar al campus" → `/campus`, el Inicio del estudiante (captura 2)
- "Hablar con AURA" → `/campus/chat`, el chat (captura 3)
- "Abrir panel" → `/coordinacion`, el resumen de la red (captura 4)

## 2. Qué tan fiel quedó a tu Figma

No pude abrir tus links de Figma (el sitio bloquea accesos automáticos),
así que trabajé directamente de las 4 capturas que mandaste: medí los
colores exactos pixel por pixel desde las imágenes (no a ojo), así que el
crema de fondo, el teal de los botones, el morado de "Coordinación de red"
y los 4 colores de las etiquetas de las stat cards deberían calzar casi
exacto. Dos cosas que no puedo garantizar sin el archivo real de Figma:

- **La tipografía.** Usé "Plus Jakarta Sans" (Google Fonts, gratis) porque
  se parece mucho a la de tus capturas, pero si tu equipo ya eligió otra
  fuente puntual, solo se cambia en `app/layout.tsx` (una línea).
- **Las pantallas que no mandaste capturas.** "Mapa de servicios", "Desencuentros" y
  "Reglas" existen como placeholders (dicen honestamente "fuera del
  alcance de este entregable") para que ningún link del sidebar se sienta
  roto si lo clickeas en el video — pero no inventé un diseño para ellas
  porque no tengo cómo saber si se parece a lo que ya pensaron.

## 3. Estructura del proyecto

```
app/
├── page.tsx                      landing
├── campus/
│   ├── layout.tsx                 PerfilProvider: el estudiante activo de la demo
│   ├── page.tsx                   Inicio
│   ├── chat/page.tsx              Conversar con AURA (agente real)
│   ├── citas/page.tsx             Mis citas (del backend; se pueden cancelar)
│   ├── cursos/page.tsx            Mis cursos (período D7, asistencia, horario semanal; datos simulados)
│   ├── calificaciones/page.tsx    Notas por curso, promedio y nota necesaria para aprobar
│   └── calendario/page.tsx        Calendario D7 + clases, evaluaciones y mis citas
└── coordinacion/                 panel de la red (usa el backend); en-vivo/ = citas nuevas en tiempo real (SSE)

components/
├── PortalShell.tsx        marco del campus (barra teal, mismo estilo que Coordinación)
├── campus/                nav, PerfilProvider y selector de estudiante (TopbarControls)
│   └── academico/         anillo, cuenta animada y colores por curso de Mis cursos, Calificaciones y Calendario
├── coordinacion/          todo el panel de Coordinación
├── chat/                  burbujas, tarjetas de opciones, comprobante de cita, «escribiendo…»
└── ui/                    Tag, StatCard, Placeholder, Estados

lib/
├── api.ts            ÚNICO lugar con fetch: chat, citas y Coordinación
├── types.ts          tipos del estudiante (snake_case, como el backend)
├── perfiles.ts       los estudiantes de la demo (ver abajo)
└── servicios-ui.ts   color, ícono y etiqueta de cada tipo de servicio y canal
```

La regla de oro: **los componentes nunca llaman a `fetch` directamente**, siempre pasan por una función
de `lib/api.ts`.

### Estudiantes de la demo

`lib/perfiles.ts` define los perfiles (ciudad ficticia de Aethera). El selector «Demo · Lucía» de la barra
superior cambia de estudiante de verdad: cada uno tiene su chat y sus citas en el backend. Lo que se envía:

| Campo del perfil | Va al backend como | Notas |
|---|---|---|
| `id` (`STU_DEMO_###`) | `estudiante_id` | No choca con los ids de los datos (`STU_AE_######`) |
| `distrito` (uno de los 5 de D6) | `distrito` en `POST /api/chat` | Distrito donde vive; se usa para citas presenciales. En la conversación se puede cambiar |
| — | — | El turno diurno/nocturno **no** es parte del perfil: el agente lo toma de lo que la persona cuente |

Para agregar un perfil basta añadir un objeto a `PERFILES`.

### En vivo (para el video con dos pantallas)

`/coordinacion/en-vivo` muestra, al instante y sin recargar, cada cita que un estudiante reserva o cancela
y cada solicitud sin cupo que registra el agente. Además aparece un aviso emergente en cualquier pantalla
de Coordinación, la insignia de «En vivo» en la barra lateral cuenta lo no visto y los números del panel
(citas agendadas, ocupación) se actualizan solos. Solo registra lo **nuevo**: las citas sembradas no
aparecen. Detalle del contrato: `src/backend/docs/api_coordinacion.md` (sección «Actividad en vivo»).

Para grabarlo: `/campus/chat` en una ventana (como cualquier perfil del selector) y `/coordinacion` en otra.

### Modo lote

Cuando un servicio llega al 75 % de utilización, sus cupos solo se reparten por **lote** (se cierra solo y asigna
con el algoritmo genético; reglas en `src/backend/docs/como_funciona.md` §8).

- **Coordinación → Lotes** (`/coordinacion/lotes`): los 15 servicios con la marca del 75 %, el lote abierto con su
  cuenta regresiva y las solicitudes que lleva, y el historial con la comparación genético vs orden de llegada.
  «En vivo» muestra también cuándo un servicio cruza el umbral y cada novedad del lote.
- **Estudiante** (`/campus/chat`): si todo lo compatible está en modo lote, el chat muestra una tarjeta con el botón
  «Entrar al lote»; al aceptar aparece un anillo con la cuenta regresiva y, cuando el lote se cierra, la cita llega
  sola al chat (y a «Mis citas») por el flujo de avisos, sin enviar ningún mensaje.

Para el video: abre `/campus/chat` en dos ventanas (como dos perfiles del selector) y `/coordinacion/lotes` en otra.

### Cómo se ve el chat

- Al abrir, AURA saluda y avisa qué distrito usa; hay sugerencias para empezar.
- Cuando el agente propone citas, salen como **tarjetas** (color por tipo de servicio). Al tocar una se le
  responde «quiero la opción N» al agente, que es quien reserva. La tarjeta no reserva por sí sola.
- Una cita reservada aparece como comprobante; una cancelada, como aviso. Un mensaje de crisis se destaca.
- Paleta y animaciones: las mismas `co.*` del panel de Coordinación (`tailwind.config.ts`); las animaciones
  respetan `prefers-reduced-motion`.

## 4. Endpoints que usa el estudiante

| Endpoint | Método | Función en `lib/api.ts` |
|---|---|---|
| `/api/chat` | `POST` | `chatEnviar()` |
| `/api/chat/{session_id}?estudiante_id=` | `GET` / `DELETE` | `chatHistorial()` / `chatReiniciar()` |
| `/api/appointments?estudiante_id=` | `GET` | `getMisCitas()` |
| `/api/appointments/{id}?estudiante_id=` | `DELETE` | `cancelarCita()` |
| `/api/demo/estado` | `GET` | `getDemoEstado()` (fecha simulada en Inicio) |

Parámetros y respuestas: `src/backend/docs/api_agente.md`.

## 5. Conectar el backend

1. Copia `.env.local.example` a `.env.local` (por defecto `http://localhost:8080`).
2. Backend: `uvicorn app.main:app --port 8080` en `src/backend` (con `requirements-agente.txt` instalado) y
   `ollama serve`.
3. `npm run dev`.

## 6. Desplegar para el video y el Demo Day

1. Sube el proyecto a un repositorio de GitHub.
2. Entra a https://vercel.com, conecta tu GitHub e importa el repo.
3. Si ya tienes `NEXT_PUBLIC_API_URL`, agrégalo en Vercel (Project Settings
   → Environment Variables).
4. Deploy. Te da una URL pública para el video y para el Demo Day.

## 7. Checklist antes de grabar

- [ ] Flujo completo sin errores: Inicio → Hablar con AURA → contar qué
      necesitas → tocar una tarjeta → comprobante en el chat → aparece en
      "Mis citas" → cancelar.
- [ ] Cambiar de estudiante con el selector: cada uno ve su chat y sus citas.
- [ ] Comparaste lado a lado con el Figma — si algo no calza (tipografía,
      algún espaciado), es ajustable en minutos, avísame.
- [ ] Backend y Ollama encendidos (`GET /api/chat/estado` dice «Listo»).
- [ ] Mencionas en el video qué datasets alimentan lo que ves en pantalla.
