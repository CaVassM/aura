# Backend de AURA (FastAPI + agente LangChain). Se construye desde src/backend:
#   docker build -t aura-backend src/backend
# El Data Pack NO va en la imagen: se monta como volumen en /data (AURA_DATA_DIR).
# Ollama corre fuera del contenedor (en tu PC): AURA_OLLAMA_URL apunta a él.

# Dependencias: pyproject.toml + uv.lock (versiones exactas). Ver pyproject.toml.
FROM python:3.12-slim

# Variables de entorno para Python, pip y uv.
# PYTHONDONTWRITEBYTECODE=1: evita que Python cree archivos .pyc
# PYTHONUNBUFFERED=1: evita buffering en stdout/stderr, asi los logs se ven en tiempo real.
# PIP_NO_CACHE_DIR=1: evita que pip guarde cache de paquetes descargados.
# PIP_DISABLE_PIP_VERSION_CHECK=1: evita que pip pierda tiempo revisando si hay una nueva version de pip desde el internet.
# UV_PYTHON_DOWNLOADS=never: uv usa el Python 3.12 de la imagen, no descarga otro.
# UV_LINK_MODE=copy: uv copia los paquetes en vez de enlazarlos (el cache no está en la imagen).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

# Creamos un directorio de trabajo, este es el /app.
WORKDIR /app

# uv instala exactamente lo que dice uv.lock (versión de uv fijada).
RUN pip install --no-cache-dir uv==0.13.1

# Dependencias primero (capa cacheable). --frozen falla si uv.lock no coincide con pyproject.toml.
# --no-dev: sin pytest ni matplotlib. --extra agente: incluye LangChain + Ollama.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra agente --no-install-project
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

# Usuario sin privilegios
RUN useradd --system --create-home --uid 10001 aura && chown -R aura:aura /app
USER aura

ENV AURA_DATA_DIR=/data
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/salud', timeout=4).status == 200 else 1)"

# Un solo proceso: todo el estado vive en RAM (un worker, nunca más).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
