"""Пользователь: users, favorites, preferences, interactions (аналитика)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    ACTION_CLICK_SOURCE,
    CategoryORM,
    EventInteractionORM,
    EventORM,
    FavoriteORM,
    UserORM,
    UserPreferencesORM,
)


async def get_or_create(db: AsyncSession, external_id: str) -> UserORM:
    result = await db.execute(select(UserORM).where(UserORM.external_id == external_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = UserORM(external_id=external_id)
        db.add(user)
        await db.flush()
    return user


async def get_preferences(
    db: AsyncSession, external_id: Optional[str]
) -> Optional[UserPreferencesORM]:
    """Прочитать предпочтения, не создавая пользователя (для soft-ранжирования)."""
    if external_id is None:
        return None
    result = await db.execute(
        select(UserPreferencesORM)
        .join(UserORM, UserORM.id == UserPreferencesORM.user_id)
        .where(UserORM.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def upsert_preferences(
    db: AsyncSession,
    external_id: str,
    categories: list[str],
    price_max: Optional[int],
    radius_km: Optional[float],
) -> UserPreferencesORM:
    user = await get_or_create(db, external_id)
    result = await db.execute(
        select(UserPreferencesORM).where(UserPreferencesORM.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = UserPreferencesORM(user_id=user.id)
        db.add(prefs)
    else:
        prefs.updated_at = datetime.now(timezone.utc)
    prefs.categories = categories
    prefs.price_max = price_max
    prefs.radius_km = radius_km
    await db.flush()
    return prefs


async def add_favorite(db: AsyncSession, external_id: str, event_id: int) -> FavoriteORM:
    user = await get_or_create(db, external_id)
    result = await db.execute(
        select(FavoriteORM).where(
            FavoriteORM.user_id == user.id, FavoriteORM.event_id == event_id
        )
    )
    fav = result.scalar_one_or_none()
    if fav is None:
        fav = FavoriteORM(user_id=user.id, event_id=event_id)
        db.add(fav)
        await db.flush()
    return fav


async def remove_favorite(db: AsyncSession, external_id: str, event_id: int) -> bool:
    result = await db.execute(
        select(UserORM.id).where(UserORM.external_id == external_id)
    )
    user_id = result.scalar_one_or_none()
    if user_id is None:
        return False
    result = await db.execute(
        delete(FavoriteORM).where(
            FavoriteORM.user_id == user_id, FavoriteORM.event_id == event_id
        )
    )
    return (result.rowcount or 0) > 0


async def list_favorites(
    db: AsyncSession,
    external_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[tuple[FavoriteORM, EventORM]], int]:
    result = await db.execute(
        select(UserORM.id).where(UserORM.external_id == external_id)
    )
    user_id = result.scalar_one_or_none()
    if user_id is None:
        return [], 0
    count_stmt = select(func.count()).select_from(FavoriteORM).where(
        FavoriteORM.user_id == user_id
    )
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = (
        select(FavoriteORM, EventORM)
        .join(EventORM, EventORM.id == FavoriteORM.event_id)
        .where(FavoriteORM.user_id == user_id)
        .order_by(FavoriteORM.added_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = [(fav, event) for fav, event in result.all()]
    return rows, total


async def log_interaction(
    db: AsyncSession,
    external_id: Optional[str],
    event_id: int,
    action: str,
    meta: Optional[dict] = None,
) -> None:
    user = await get_or_create(db, external_id) if external_id else None
    db.add(
        EventInteractionORM(
            user_id=user.id if user else None,
            event_id=event_id,
            action=action,
            meta=meta,
        )
    )
    await db.flush()


async def interactions_summary(db: AsyncSession, external_id: str) -> dict:
    result = await db.execute(select(UserORM.id).where(UserORM.external_id == external_id))
    user_id = result.scalar_one_or_none()

    clicks = favorites = 0
    top: dict[str, int] = {}
    if user_id is not None:
        clicks = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(EventInteractionORM)
                    .where(
                        EventInteractionORM.user_id == user_id,
                        EventInteractionORM.action == ACTION_CLICK_SOURCE,
                    )
                )
            ).scalar_one()
        )
        favorites = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(FavoriteORM)
                    .where(FavoriteORM.user_id == user_id)
                )
            ).scalar_one()
        )
        rows = (
            await db.execute(
                select(CategoryORM.slug, func.count())
                .join(EventORM, EventORM.category_id == CategoryORM.id)
                .join(
                    EventInteractionORM,
                    EventInteractionORM.event_id == EventORM.id,
                )
                .where(
                    EventInteractionORM.user_id == user_id,
                    EventInteractionORM.action == ACTION_CLICK_SOURCE,
                )
                .group_by(CategoryORM.slug)
                .order_by(func.count().desc())
            )
        ).all()
        top = {slug: int(n) for slug, n in rows}

    return {
        "user_id": external_id,
        "clicks_to_source": clicks,
        "favorites": favorites,
        "top_categories": top,
    }
