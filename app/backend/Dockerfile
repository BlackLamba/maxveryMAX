# Backend maxveryMAX. Контекст сборки — корень app/ (нужен shared/).
#   docker compose build  (см. app/docker-compose.yml)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# зависимости первым слоем — кэш между сборками
# (backend/requirements.txt ссылается на корневой -r ../requirements.txt)
COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# общий код и модуль backend (тесты не нужны в образе, но малы — берём для parity)
COPY shared/ ./shared/
COPY infra/ ./infra/
COPY backend/ ./backend/

WORKDIR /app/backend
EXPOSE 8000

# ждём БД → применяем миграции → поднимает uvicorn
CMD ["sh", "-c", "python /app/infra/scripts/wait_for_db.py && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
