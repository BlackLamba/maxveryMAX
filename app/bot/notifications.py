"""
Фоновый цикл рассылки уведомлений (Could Have, не блокирует основной сценарий).

Схема работы (см. Аналитик/06_MAX_и_UX.md, раздел 4):
  1. Раз в NOTIFICATIONS_POLL_INTERVAL_SECONDS опрашиваем backend:
       GET /api/notifications/pending
  2. Для каждого уведомления отправляем сообщение пользователю через Bot API.
  3. После успешной отправки подтверждаем бэкенду:
       POST /api/notifications/{id}/ack

Особые случаи:
  - Эндпоинты на бэке могут ещё отсутствовать — просто пропускаем цикл.
  - Пользователь заблокировал бота — ЛОГИРУЕМ и продолжаем остальным,
    не роняем весь цикл.
  - Сетевые ошибки — логируем, спим дальше.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from maxapi import Bot
from maxapi.exceptions import MaxApiError

from . import config, texts
from .api_client import BackendClient

logger = logging.getLogger(__name__)

# MAX-код ошибки "пользователь заблокировал бота / не может получить сообщение".
# По документации и наблюдениям это обычно 403 c кодом FORBIDDEN /
# CHAT_NOT_FOUND / USER_BLOCKED. Обрабатываем всё семейство 403 + 400 как
# "пользователь недоступен" — лучше пропустить одно уведомление, чем упасть.
_BLOCKED_STATUSES = {400, 403, 404}


def _format_notification_text(notification: dict[str, Any]) -> str:
    """Собирает текст уведомления по данным из бэкенда."""
    ntype = notification.get("type", "reminder")
    title = notification.get("event_title") or "событие"
    when = notification.get("when") or "скоро"
    place = notification.get("place") or ""
    change_description = notification.get("change_description") or ""

    if ntype == "change" and change_description:
        return texts.NOTIFICATION_CHANGE_TEMPLATE.format(
            title=title,
            change_description=change_description,
        )
    return texts.NOTIFICATION_REMINDER_TEMPLATE.format(
        title=title, when=when, place=place
    )


async def _send_one(bot: Bot, notification: dict[str, Any]) -> bool:
    """Отправляет одно уведомление. Возвращает True при успехе."""
    user_id = notification.get("user_id")
    if not user_id:
        logger.warning("В уведомлении нет user_id: %s", notification.get("id"))
        return False

    text = _format_notification_text(notification)

    # NOTE: по архитектуре deep link в конкретную карточку должен приходить
    # из бэкенда в поле `deeplink` или `startapp_payload`. Пока (Could Have
    # этап) у бэка таких полей нет — отправляем просто текст с напоминанием.
    # Когда эндпоинт начнёт отдавать payload, сюда добавим inline-кнопку
    # OpenAppButton с этим payload (аналогично хендлеру /start).
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
        )
        return True
    except MaxApiError as exc:
        status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if status in _BLOCKED_STATUSES:
            logger.info(
                "Пользователь %s недоступен (статус %s) — уведомление %s пропущено",
                user_id,
                status,
                notification.get("id"),
            )
        else:
            logger.warning(
                "Не удалось отправить уведомление %s пользователю %s: %s",
                notification.get("id"),
                user_id,
                exc,
            )
        return False
    except Exception as exc:  # noqa: BLE001 — не даём упасть всему циклу
        logger.exception(
            "Неожиданная ошибка при отправке уведомления %s: %s",
            notification.get("id"),
            exc,
        )
        return False


async def run_notifications_loop(bot: Bot, api: BackendClient) -> None:
    """Бесконечный цикл: опрос бэка → рассылка → ack → сон."""
    interval = config.NOTIFICATIONS_POLL_INTERVAL_SECONDS
    logger.info(
        "Фоновый цикл уведомлений запущен (интервал %s сек)", interval
    )
    while True:
        try:
            notifications = await api.fetch_pending_notifications()
            if notifications:
                logger.info("Получено %s уведомлений для рассылки", len(notifications))
            for n in notifications:
                nid = n.get("id")
                sent = await _send_one(bot, n)
                if sent:
                    await api.ack_notification(nid)
                # Маленькая пауза между отправками, чтобы не упереться в рейтлимит
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("Цикл уведомлений остановлен")
            raise
        except Exception as exc:  # noqa: BLE001 — любая ошибка только логируется
            logger.exception("Ошибка в цикле уведомлений: %s", exc)

        await asyncio.sleep(interval)
