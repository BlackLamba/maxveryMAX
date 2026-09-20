"""
Асинхронный HTTP-клиент к backend.

ВАЖНОЕ правило проекта: бот НИКОГДА не ходит напрямую в БД и не обращается
к внешним афишам. Все данные — только через backend по HTTP.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from . import config

logger = logging.getLogger(__name__)


class BackendClient:
    """Тонкая обёртка над httpx.AsyncClient под нужные боту эндпоинты."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self._base_url = (base_url or config.BACKEND_URL).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"User-Agent": "maxveryMAX-bot/0.1.0"},
            )

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("BackendClient не инициализирован: вызовите .start()")
        return self._client

    # --- healthcheck -------------------------------------------------------

    async def health(self) -> bool:
        """Проверка, что backend жив. Используется при старте бота."""
        try:
            r = await self.client.get("/api/health")
            return r.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("Backend недоступен: %s", exc)
            return False

    # --- notifications (Could Have, не блокирует запуск) -------------------

    async def fetch_pending_notifications(self) -> list[dict[str, Any]]:
        """
        Запрашивает у backend список уведомлений, ожидающих рассылки.
        Если эндпоинт ещё не реализован на бэке (404) или отвечает ошибкой —
        возвращаем пустой список и НЕ ПАДАЕМ. Это отдельная задача Жени.
        """
        try:
            r = await self.client.get("/api/notifications/pending")
            if r.status_code == 404:
                logger.debug("Эндпоинт /api/notifications/pending ещё не готов на бэке")
                return []
            r.raise_for_status()
            data = r.json()
            # Бэкенд может отдавать как список, так как {"items": [...]}
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return data["items"]
            return []
        except httpx.HTTPError as exc:
            logger.warning("Не удалось получить pending-уведомления: %s", exc)
            return []
        except ValueError:  # invalid JSON
            logger.warning("Бэкенд отдал не-JSON на /api/notifications/pending")
            return []

    async def ack_notification(self, notification_id: Any) -> bool:
        """Подтверждает бэкенду, что уведомление успешно отправлено."""
        try:
            r = await self.client.post(f"/api/notifications/{notification_id}/ack")
            if r.status_code == 404:
                logger.debug(
                    "Эндпоинт /api/notifications/%s/ack ещё не готов на бэке",
                    notification_id,
                )
                return False
            r.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning(
                "Не удалось подтвердить уведомление %s: %s", notification_id, exc
            )
            return False
