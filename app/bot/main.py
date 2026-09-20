"""
Точка входа бота.

Использует long polling для разработки (по умолчанию для хакатон-проекта),
плюс запускает фоновый цикл уведомлений после успешной инициализации.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from maxapi import Bot

from . import config
from .api_client import BackendClient
from .handlers import dp
from .notifications import run_notifications_loop


def _setup_logging() -> None:
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def _main_async() -> None:
    _setup_logging()
    logger = logging.getLogger("bot")

    if not config.MAX_BOT_TOKEN:
        logger.error(
            "MAX_BOT_TOKEN не задан! Укажите токен бота в .env "
            "(см. app/.env.example)."
        )
        sys.exit(1)

    logger.info("Инициализация бота %s...", config.BOT_NAME)

    bot = Bot(token=config.MAX_BOT_TOKEN)

    # Инициализируем клиент к backend'у и проверяем, что он жив.
    # Бэк может подниматься чуть позже бота — это не фатально, просто предупреждаем.
    api = BackendClient()
    await api.start()
    if await api.health():
        logger.info("Backend доступен по %s", config.BACKEND_URL)
    else:
        logger.warning(
            "Backend пока не отвечает на /api/health (это нормально, если он поднимается). "
            "Продолжаю запуск."
        )

    # Фоновая задача с уведомлениями. Если эндпоинты ещё не готовы —
    # цикл будет просто спать и логировать debug, не мешая работе бота.
    notifications_task = asyncio.create_task(run_notifications_loop(bot, api))

    try:
        logger.info("Запускаю long polling...")
        await dp.start_polling(bot)
    finally:
        logger.info("Останавливаю бота...")
        notifications_task.cancel()
        try:
            await notifications_task
        except asyncio.CancelledError:
            pass
        await api.stop()


def main() -> None:
    try:
        asyncio.run(_main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
