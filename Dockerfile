FROM python:3.11.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STANZA_RESOURCES_DIR=/opt/stanza_resources
ENV TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /opt/stanza_resources \
    && python -c "import stanza; stanza.download('ca', model_dir='/opt/stanza_resources', verbose=False)"

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl --fail --silent --show-error http://127.0.0.1:${PORT:-7860}/health || exit 1

CMD ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT:-7860} --workers 1 --threads 4 --timeout 600"]
