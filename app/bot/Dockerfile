# Бот maxveryMAX. Контекст сборки — корень app/ (нужен shared/ на будущее).
#   docker compose --profile full build bot
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Зависимости первым слоем — кэш между сборками.
COPY requirements.txt ./requirements.txt
COPY bot/requirements.txt ./bot/requirements.txt
RUN pip install --no-cache-dir -r bot/requirements.txt

# Общий код (понадобится, когда бот будет отправлять уведомления с deep link,
# использующим общие enum/модели; пока не импортируется, но копируем по стилю
# остальных модулей, чтобы структура была единообразной).
COPY shared/ ./shared/

# Код самого бота.
COPY bot/ ./bot/

WORKDIR /app

# Токен и URL'ы приходят из окружения (docker-compose + .env), здесь — никаких секретов.
CMD ["python", "-m", "bot.main"]
