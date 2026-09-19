"""Логирование переходов пользователя на официальный источник.

Это то, на чём меряется метрика пилота «доля пользователей, дошедших до
перехода» (08_пилотный_запуск.md). Записи — в event_interactions.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ACTION_CLICK_SOURCE, EventInteractionORM
from ..repositories import events_repo, user_repo


async def log_click(
    db: AsyncSession,
    event_id: int,
    user_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> None:
    event = await events_repo.get(db, event_id)
    if event is None:
        from ..errors import ApiNotFound

        raise ApiNotFound(f"событие {event_id} не найдено")

    user = await user_repo.get_or_create(db, user_id) if user_id else None
    db.add(
        EventInteractionORM(
            user_id=user.id if user else None,
            event_id=event_id,
            action=ACTION_CLICK_SOURCE,
            meta=meta,
        )
    )
    await db.commit()
