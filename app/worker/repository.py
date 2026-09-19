from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import (  # type: ignore[import-not-found]
    EventORM,
    EventSourceORM,
    EventTagORM,
)
from app.models.reference import (  # type: ignore[import-not-found]
    CategoryORM,
    CityORM,
    TagORM,
)
from shared.models import Event  # type: ignore[import-not-found]

from .pipeline.quality import quality_score

log = logging.getLogger(__name__)


def _normalize_tag(raw: str) -> str:
    return raw.strip().lower()


async def _city_id(session: AsyncSession, slug: str) -> int:
    row = await session.scalar(select(CityORM).where(CityORM.slug == slug))
    if row is None:
        raise ValueError(f"Unknown city_slug={slug!r}; добавь город в справочник cities")
    return row.id


async def _category_id(session: AsyncSession, slug: str) -> int:
    row = await session.scalar(select(CategoryORM).where(CategoryORM.slug == slug))
    if row is None:
        raise ValueError(
            f"Unknown category slug={slug!r}; добавь категорию в справочник categories"
        )
    return row.id


async def _upsert_tags(session: AsyncSession, tags: list[str]) -> list[int]:
    """Таблица tags: id, name (unique). Ищем/создаём по name."""
    normalized = sorted({_normalize_tag(t) for t in tags if t and t.strip()})
    if not normalized:
        return []

    existing = await session.scalars(select(TagORM).where(TagORM.name.in_(normalized)))
    by_name = {t.name: t for t in existing}

    ids: list[int] = []
    for name in normalized:
        tag = by_name.get(name)
        if tag is None:
            tag = TagORM(name=name)
            session.add(tag)
            await session.flush()
            by_name[name] = tag
        ids.append(tag.id)
    return ids


async def upsert_event(session: AsyncSession, event: Event) -> EventORM:
    """Идемпотентный upsert.

    1. Ищем event_sources по (source, source_id).
    2. Если нашли — обновляем events.
    3. Если нет — создаём events + event_sources.
    4. Синхронизируем event_tags.
    """
    city_id = await _city_id(session, event.city_slug)
    category_id = await _category_id(session, event.category.value)

    source_row = await session.scalar(
        select(EventSourceORM)
        .options(selectinload(EventSourceORM.event))
        .where(
            EventSourceORM.source == event.source,
            EventSourceORM.source_id == event.source_id,
        )
    )

    if source_row is not None:
        orm = source_row.event
        orm.title = event.title
        orm.description = event.description
        orm.category_id = category_id
        orm.city_id = city_id
        orm.provider = event.provider
        orm.venue_name = event.venue_name
        orm.address = event.address
        orm.lat = event.lat
        orm.lon = event.lon
        orm.starts_at = event.starts_at
        orm.ends_at = event.ends_at
        orm.price_min = event.price_min
        orm.price_max = event.price_max
        orm.is_free = event.is_free
        orm.age_limit = event.age_limit
        orm.image_url = event.image_url
        orm.source_url = event.source_url
        orm.data_origin = event.data_origin
        orm.status = event.status
        orm.quality_score = quality_score(event)
        source_row.source_url = event.source_url
        source_row.raw = event.model_dump(mode="json")
    else:
        orm = EventORM(
            title=event.title,
            description=event.description,
            category_id=category_id,
            city_id=city_id,
            provider=event.provider,
            venue_name=event.venue_name,
            address=event.address,
            lat=event.lat,
            lon=event.lon,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            price_min=event.price_min,
            price_max=event.price_max,
            is_free=event.is_free,
            age_limit=event.age_limit,
            image_url=event.image_url,
            source_url=event.source_url,
            data_origin=event.data_origin,
            status=event.status,
            quality_score=quality_score(event),
        )
        session.add(orm)
        await session.flush()
        session.add(
            EventSourceORM(
                event_id=orm.id,
                source=event.source,
                source_id=event.source_id,
                source_url=event.source_url,
                raw=event.model_dump(mode="json"),
            )
        )

    # tags
    tag_ids = await _upsert_tags(session, event.tags)
    await session.execute(
        EventTagORM.__table__.delete().where(EventTagORM.event_id == orm.id)
    )
    for tag_id in tag_ids:
        session.add(EventTagORM(event_id=orm.id, tag_id=tag_id))

    return orm


async def upsert_many(session: AsyncSession, events: list[Event]) -> int:
    count = 0
    for event in events:
        try:
            await upsert_event(session, event)
            count += 1
        except Exception:
            log.exception("Failed to upsert event source_id=%s", event.source_id)
    await session.commit()
    return count