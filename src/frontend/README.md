# AURA — Frontend (Entregable 2)

Réplica funcional de tu prototipo de Figma: landing → campus virtual del
estudiante → chat con AURA → panel de coordinación de la red. Todo corre hoy
con datos simulados (mock) para que lo puedas mostrar funcionando sin
esperar al backend de Camilo; está armado para que conectar el backend real
sea cambiar un solo archivo (`lib/api.ts`).

> **Coordinación ya usa el backend real.** Las cuatro pantallas de `/coordinacion`
> (Resumen, Mapa de servicios, Desencuentros y Reglas) leen de la API FastAPI de
> `src/backend` a través de `lib/api.ts` (tipos en `lib/types-coordinacion.ts`).
> Para verlas hay que levantar el backend (`uvicorn app.main:app --port 8080` en
> `src/backend`) y definir `NEXT_PUBLIC_API_URL` en `.env.local`; si el backend no
> responde, el panel muestra un mensaje de error con botón «Reintentar». El
> contrato está en `src/backend/docs/api_coordinacion.md`. La vista del estudiante
> (campus y chat) sigue con datos simulados; sus endpoints del backend usan
> snake_case, así que habrá que adaptar `lib/api.ts` y `lib/types.ts` al conectarla.

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
- **Las pantallas que no mandaste capturas.** "Mis cursos",
  "Calificaciones", "Calendario", "Mapa de servicios", "Desencuentros" y
  "Reglas" existen como placeholders (dicen honestamente "fuera del
  alcance de este entregable") para que ningún link del sidebar se sienta
  roto si lo clickeas en el video — pero no inventé un diseño para ellas
  porque no tengo cómo saber si se parece a lo que ya pensaron.

## 3. Estructura del proyecto

```
app/
├── page.tsx                      landing (captura 1)
├── campus/
│   ├── page.tsx                   Inicio (captura 2)
│   ├── chat/page.tsx               Conversar con AURA (captura 3)
│   ├── citas/page.tsx              Mis citas (nueva — lista lo agendado)
│   └── cursos|calificaciones|calendario/   placeholders
└── coordinacion/
    ├── page.tsx                   Resumen de red (captura 4)
    └── mapa|desencuentros|reglas/  placeholders

components/
├── PortalShell.tsx        layout compartido: sidebar + topbar
├── campus/                nav e identidad del campus virtual
├── coordinacion/          nav e identidad del panel de coordinación
├── chat/                  burbuja, tarjeta de servicio, selector de horario
└── ui/                    Tag, StatCard, Placeholder (piezas chicas reusadas)

lib/
├── types.ts    los "contratos" de datos
└── api.ts       TODO lo que hoy simula el backend vive aquí
```

`PortalShell` es la pieza más importante para que entiendas rápido el
proyecto: es el componente que dibuja el sidebar y el topbar (iguales en
estructura entre campus y coordinación, pero con colores/íconos/links
distintos). Cada página solo le pasa qué mostrar — no repito el sidebar
copiado y pegado en cada archivo.

La regla de oro sigue siendo la misma que la vez pasada: **los componentes
nunca llaman a `fetch` directamente**, siempre pasan por una función de
`lib/api.ts`. Hoy esas funciones simulan el backend; el día que Camilo
exponga los endpoints reales, abres ese archivo y cambias el cuerpo de cada
función por un `fetch()` — no tocas ni un componente. Ahí mismo dejé
comentado un ejemplo completo de cómo se vería.

## 4. Endpoints a acordar con Camilo y Leo

| Endpoint | Método | Para qué | Función en `lib/api.ts` |
|---|---|---|---|
| `/api/chat` | `POST` | Manda el mensaje del estudiante, recibe la respuesta del agente y, si aplica, servicios sugeridos | `sendMessage()` |
| `/api/services/:id/slots` | `GET` | Horarios disponibles de un servicio | `getAvailableSlots()` |
| `/api/appointments` | `POST` | Crea la cita | `bookAppointment()` |
| `/api/appointments` | `GET` | Lista las citas del estudiante (para "Mis citas") | `getMyAppointments()` |
| `/api/network/summary` | `GET` | Estadísticas y ocupación por servicio para el panel de coordinación | `getNetworkSummary()` |

`lib/types.ts` tiene la forma exacta de cada dato. Pásaselo a Camilo tal
cual — es la forma más rápida de que el JSON que arma el backend calce sin
ida y vuelta.

## 5. Conectar el backend real

1. Copia `.env.local.example` a `.env.local` y pon ahí la URL real.
2. En `lib/api.ts`, reemplaza el cuerpo de cada función por un `fetch()` a
   `` `${process.env.NEXT_PUBLIC_API_URL}/api/...` ``.
3. `npm run dev` de nuevo y pruebas contra el backend real.

## 6. Desplegar para el video y el Demo Day

1. Sube el proyecto a un repositorio de GitHub.
2. Entra a https://vercel.com, conecta tu GitHub e importa el repo.
3. Si ya tienes `NEXT_PUBLIC_API_URL`, agrégalo en Vercel (Project Settings
   → Environment Variables).
4. Deploy. Te da una URL pública para el video y para el Demo Day.

## 7. Checklist antes de grabar

- [ ] Flujo completo sin errores: Inicio → Hablar con AURA → elegir
      servicio → elegir horario → confirmación dentro del chat → aparece
      en "Mis citas".
- [ ] Comparaste lado a lado con el Figma — si algo no calza (tipografía,
      algún espaciado), es ajustable en minutos, avísame.
- [ ] `lib/api.ts` ya apunta al backend real (o, si todavía no está listo,
      el mock se deja tal cual — igual demuestra el flujo completo).
- [ ] Mencionas en el video qué datasets alimentan lo que ves en pantalla.
