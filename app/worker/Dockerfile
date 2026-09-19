FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# shared — общие Pydantic-модели
COPY shared /app/shared

# backend-пакет app (models, db, config) — worker их переиспользует
COPY backend/app /app/app

# сам worker
COPY worker /app/worker

CMD ["python", "-m", "worker.run"]