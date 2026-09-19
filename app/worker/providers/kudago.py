from __future__ import annotations

from datetime import datetime

from shared.models import Event  # type: ignore[import-not-found]


class KudaGoProvider:
    """Заглушка.

    Контракт: fetch_events(since, until) -> list[Event] с data_origin='live'.
    """

    name = "kudago"

    async def fetch_events(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]:
        return []