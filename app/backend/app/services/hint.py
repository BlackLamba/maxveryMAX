"""Подсказка при пустом результате: что конкретно смягчить.

Требование UX (06_MAX_и_UX.md, п. 4): не пустой экран, а явная рекомендация.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from shared.categories import CATEGORY_NAMES

from ..repositories import events_repo
from ..schemas.events import EventFilters

MAX_SENTENCES = 3


async def build_empty_hint(
    db: AsyncSession,
    f: EventFilters,
    bounds: tuple[datetime, datetime] | None,
) -> str:
    parts: list[str] = []

    if f.is_free:
        parts.append("бесплатных мероприятий в этих условиях нет — попробуйте разрешить платные")
    elif f.price_max is not None:
        min_price = await events_repo.min_price(db, f, bounds)
        if min_price is not None:
            parts.append(f"поднимите бюджет хотя бы до {min_price} ₽")

    if f.time_from is not None or f.time_to is not None:
        parts.append("расширьте временное окно (например, на весь день)")

    if f.radius_km is not None:
        parts.append("расширьте радиус поиска или уберите ограничение по расстоянию")

    if f.category:
        available = await events_repo.available_categories(db, f, bounds)
        if available:
            names = [CATEGORY_NAMES.get(slug, slug).lower() for slug in available[:4]]
            parts.append(f"на это время есть: {', '.join(names)}")

    if f.date_from is not None:
        nearest = await events_repo.nearest_event_date(db, f, _now_utc())
        if nearest is not None:
            parts.append(f"ближайшее похожее событие — {nearest:%d.%m.%Y}")

    if not parts:
        parts.append("попробуйте убрать часть фильтров — например, категорию или дату")

    return "По этим условиям ничего не нашлось. Попробуйте: " + "; ".join(parts[:MAX_SENTENCES]) + "."


def _now_utc() -> datetime:
    from datetime import datetime as _dt, timezone as _tz

    return _dt.now(_tz.utc)
