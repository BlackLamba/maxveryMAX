from __future__ import annotations

from typing import Any

from shared.models import Event  # type: ignore[import-not-found]


def normalize(raw: dict[str, Any], provider: str) -> Event:
    """Приводит сырой объект провайдера к shared.Event.

    Для mock — почти no-op. Для kudago/timepad — маппинг полей,
    парсинг дат, склейка адреса, категории, тегов.
    """
    payload = dict(raw)
    payload.setdefault("source", provider)
    payload.setdefault("provider", provider)
    payload.setdefault("data_origin", "mock" if provider == "mock" else "live")
    return Event.model_validate(payload)