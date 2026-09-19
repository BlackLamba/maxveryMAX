from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from shared.models import Event  # type: ignore[import-not-found]

from ..config import MOCK_EVENTS_PATH
from ..pipeline.normalize import normalize


class MockProvider:
    """Читает подготовленный JSON. Данные помечаются data_origin='mock'."""

    name = "mock"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or MOCK_EVENTS_PATH

    async def fetch_events(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]:
        raw_items = json.loads(self.path.read_text(encoding="utf-8"))
        events = [normalize(item, provider=self.name) for item in raw_items]
        if since:
            events = [e for e in events if e.starts_at >= since]
        if until:
            events = [e for e in events if e.starts_at <= until]
        return events