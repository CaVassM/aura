# Despliegue: frontend en Vercel, backend en tu PC

```
Navegador ──► Vercel (frontend Next.js)
    │
    └──────► https://<tu-túnel>  ──► Cloudflare Tunnel ──► tu PC: docker compose (backend) ──► Ollama (tu PC)
```

El frontend es estático para el navegador: llama directo al backend (incluidos los flujos en vivo, SSE). Por eso el backend necesita una URL pública `https`, que da el túnel de Cloudflare.

## Backend en tu PC (Docker)

```bash
cp .env.example .env            # completa TUNNEL_TOKEN y AURA_CORS_ORIGINS (tu URL de Vercel)
docker compose --profile tunnel up -d --build
docker compose logs -f backend  # ver que arranca; /api/salud debe responder {"ok": true}
```

- **Ollama** sigue corriendo en tu PC (no en Docker): el contenedor lo alcanza en `host.docker.internal:11434`. Si no responde, revisa que Ollama esté abierto y `AURA_OLLAMA_MODEL` sea el nombre exacto de `ollama list`. Para correr Ollama dentro de Docker con tu GPU: `--profile ollama` y `AURA_OLLAMA_URL=http://ollama:11434`.
- **Data Pack:** se monta en solo lectura desde `src/backend/data_pack` (o `AURA_DATA_HOST_DIR`); no va dentro de la imagen.
- **Túnel con nombre (recomendado):** crea el túnel en Cloudflare Zero Trust, copia su token en `TUNNEL_TOKEN` y, en el panel, apunta el hostname público a `http://backend:8080`.
- **Túnel rápido (pruebas):** `docker compose --profile tunnel-rapido up -d` y mira la URL `https://….trycloudflare.com` en `docker compose logs tunnel-rapido`. Cambia en cada arranque, así que habría que actualizar la variable en Vercel y volver a desplegar.
- Si ya corres `cloudflared` directamente en Windows, no uses el perfil `tunnel`: apunta tu túnel a `http://localhost:8080` (el compose publica el backend solo en `127.0.0.1:8080`).

## Frontend en Vercel

1. Crea el proyecto desde el repo con **Root Directory = `src/frontend`** (el `vercel.json` de esa carpeta ya fija `npm ci`).
2. Variable de entorno (Production): `NEXT_PUBLIC_API_URL = https://<tu-hostname-del-túnel>`. Se incorpora al compilar: si cambia la URL, hay que volver a desplegar.
3. Despliegue automático: el workflow `.github/workflows/frontend.yaml` verifica (`npm ci`, tipos, build) y publica al actualizar `main`. Necesita los secretos `VERCEL_TOKEN`, `VERCEL_ORG_ID` y `VERCEL_PROJECT_ID`. Si prefieres la integración de Vercel con Git, no agregues los secretos: el job de despliegue se salta solo.
4. Previsualizaciones de Vercel: agrega `AURA_CORS_ORIGIN_REGEX=https://tu-proyecto-.*\.vercel\.app` en `.env` para que el backend las acepte.

## Ojo con la seguridad

El backend **no tiene autenticación**: cualquiera con la URL del túnel puede agendar citas y usar tu GPU a través del agente. CORS solo protege a los navegadores. Para el video no hace falta más, pero mientras esté expuesto conviene: mantener el hostname en privado, apagar el túnel (`docker compose --profile tunnel down`) cuando no se use, y, si se deja abierto, protegerlo con Cloudflare Access.

El estado vive en RAM y en un solo proceso: al reiniciar el contenedor se pierden citas y conversaciones, y no se debe escalar a más de una réplica.
