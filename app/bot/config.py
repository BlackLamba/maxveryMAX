from __future__ import annotations

import os

#: Токен бота MAX (обязательно; без него бот не запустится).
MAX_BOT_TOKEN: str = os.environ.get("MAX_BOT_TOKEN", "")

#: Ник бота в MAX (используется для сборки deep link и как имя в приветствии).
BOT_NAME: str = os.environ.get("BOT_NAME", "maxveryMAX")

#: Базовый URL backend'а. Бот ходит ТОЛЬКО сюда, никогда напрямую в БД.
BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")

#: Базовый URL мини-приложения (для fallback-ссылки, если open_app кнопка
#  по какой-то причине не поддерживается клиентом).
MINIAPP_BASE_URL: str = os.environ.get("MINIAPP_BASE_URL", "http://localhost:3000").rstrip("/")

#: Интервал опроса backend'а на предмет ожидающих уведомлений, секунд.
NOTIFICATIONS_POLL_INTERVAL_SECONDS: int = int(
    os.environ.get("NOTIFICATIONS_POLL_INTERVAL_SECONDS", "30")
)

#: Уровень логирования.
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
