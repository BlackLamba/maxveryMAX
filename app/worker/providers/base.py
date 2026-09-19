from __future__ import annotations

from datetime import datetime
from typing import Protocol

from shared.models import Event  # type: ignore[import-not-found]


class EventProvider(Protocol):
    """Контракт провайдера источника.

    Реализации: mock, kudago, timepad, culture.
    Один и тот же интерфейс для моковых и реальных источников —
    pipeline и repository о провайдере ничего не знают.
    """

    name: str

    async def fetch_events(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]: ...