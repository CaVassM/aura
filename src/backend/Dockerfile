# Backend de AURA (FastAPI + agente LangChain). Se construye desde src/backend:
#   docker build -t aura-backend src/backend
# El Data Pack NO va en la imagen: se monta como volumen en /data (AURA_DATA_DIR).
# Ollama corre fuera del contenedor (en tu PC): AURA_OLLAMA_URL apunta a él.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias primero (capa cacheable). matplotlib y pytest son solo de experimentos/pruebas: no van en runtime.
COPY requirements.txt requirements-agente.txt ./
RUN sed -e '/^matplotlib/d' -e '/^pytest/d' requirements.txt > requirements-runtime.txt \
    && grep -v '^-r' requirements-agente.txt >> requirements-runtime.txt \
    && pip install -r requirements-runtime.txt

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
