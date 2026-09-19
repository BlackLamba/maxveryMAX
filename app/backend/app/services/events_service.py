"""Оркестрация поиска: фильтры → SQL → ранжирование → reason → конверт."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..errors import ApiNotFound
from ..models import EventORM
from ..repositories import events_repo, references_repo, user_repo
from ..schemas.common import Envelope
from ..schemas.events import EventFilters, EventOut
from . import hint
from .ranking import RankContext, evaluate, haversine_km
from .timeutils import date_range_utc, window_utc_bounds

PROVIDER_NAMES = {
    "mock": "Демо-набор",
    "timepad": "ТаймПэд",
    "kudago": "KudaGo",
    "culture": "Культура.РФ",
}


def price_display(e: EventORM) -> str:
    if e.is_free or e.price_min == 0:
        return "Бесплатно"
    if e.price_min is None:
        return "Цена уточняется"
    if e.price_max is None or e.price_max <= e.price_min:
        return f"{e.price_min} ₽"
    return f"{e.price_min}–{e.price_max} ₽"


def event_to_out(
    e: EventORM,
    *,
    distance_km: Optional[float] = None,
    reason: Optional[str] = None,
    score: Optional[float] = None,
) -> EventOut:
    return EventOut(
        id=e.id,
        title=e.title,
        description=e.description or "",
        category=e.category.slug,
        category_name=e.category.name,
        city_id=e.city_id,
        city_slug=e.city.slug,
        city_name=e.city.name,
        venue_name=e.venue_name,
        address=e.address,
        lat=e.lat,
        lon=e.lon,
        distance_km=round(distance_km, 1) if distance_km is not None else None,
        starts_at=e.starts_at,
        ends_at=e.ends_at,
        price_min=e.price_min,
        price_max=e.price_max,
        is_free=bool(e.is_free),
        price_display=price_display(e),
        age_limit=e.age_limit,
        image_url=e.image_url,
        source_url=e.source_url,
        provider=PROVIDER_NAMES.get(e.provider, e.provider),
        data_origin=e.data_origin,
        quality_score=e.quality_score or 0,
        updated_at=e.updated_at,
        reason=reason,
        score=round(score, 1) if score is not None else None,
    )


async def _resolve_offset(db: AsyncSession, city_id: Optional[int]) -> int:
    offset = await references_repo.city_tz_offset(db, city_id)
    if offset is not None:
        return offset
    return get_settings().default_tz_offset_hours


async def _build_context(
    db: AsyncSession, f: EventFilters, bounds, offset_hours: int
) -> RankContext:
    prefs = await user_repo.get_preferences(db, f.user_id)
    return RankContext(
        date_from=f.date_from,
        date_to=f.date_to,
        window_start=bounds[0] if (f.time_from is not None or f.time_to is not None) else None,
        window_end=bounds[1] if (f.time_from is not None or f.time_to is not None) else None,
        price_max=f.price_max,
        is_free=f.is_free,
        lat=f.lat,
        lon=f.lon,
        radius_km=f.radius_km,
        pref_categories=frozenset(prefs.categories or []) if prefs else frozenset(),
        tz_offset_hours=offset_hours,
    )


def _bounds_for(f: EventFilters, offset_hours: int):
    if f.time_from is not None or f.time_to is not None:
        assert f.date_from is not None and f.date_from == f.date_to
        return window_utc_bounds(f.date_from, f.time_from, f.time_to, offset_hours)
    if f.date_from or f.date_to:
        d_from = f.date_from or f.date_to
        d_to = f.date_to or f.date_from
        return date_range_utc(d_from, d_to, offset_hours)
    return None


async def search_events(db: AsyncSession, f: EventFilters) -> Envelope[EventOut]:
    """Единая точка поиска: GET /api/events и POST /api/search."""
    offset_hours = await _resolve_offset(db, f.city_id)
    bounds = _bounds_for(f, offset_hours)
    ctx = await _build_context(db, f, bounds, offset_hours)

    total = await events_repo.count(db, f, bounds)
    if total == 0:
        h = await hint.build_empty_hint(db, f, bounds)
        return Envelope(items=[], total=0, hint=h)

    rows = await events_repo.fetch(
        db, f, bounds, max_candidates=get_settings().max_candidates
    )

    items: list[EventOut] = []
    scored: list[tuple[float, EventOut]] = []
    for e in rows:
        score, reason = evaluate(e, e.category.slug, ctx)
        dist = (
            haversine_km(f.lat, f.lon, e.lat, e.lon)
            if (f.lat is not None and f.lon is not None and e.lat is not None and e.lon is not None)
            else None
        )
        out = event_to_out(e, distance_km=dist, reason=reason, score=score)
        if f.sort == "relevance":
            scored.append((score, out))
        else:
            items.append(out)

    if f.sort == "relevance":
        scored.sort(key=lambda pair: (-pair[0], pair[1].starts_at))
        items = [out for _, out in scored[f.offset : f.offset + f.limit]]

    return Envelope(items=items, total=total, hint=None)


async def event_detail(db: AsyncSession, event_id: int, f: EventFilters) -> EventOut:
    """Карточка события; необязательные фильтры влияют только на reason."""
    e = await events_repo.get(db, event_id)
    if e is None:
        raise ApiNotFound(f"событие {event_id} не найдено")

    offset_hours = await _resolve_offset(db, e.city_id)
    bounds = None
    if f.time_from is not None or f.time_to is not None:
        assert f.date_from is not None and f.date_from == f.date_to
        bounds = window_utc_bounds(f.date_from, f.time_from, f.time_to, offset_hours)
    ctx = await _build_context(db, f, bounds, offset_hours)
    score, reason = evaluate(e, e.category.slug, ctx)
    dist = (
        haversine_km(f.lat, f.lon, e.lat, e.lon)
        if (f.lat is not None and f.lon is not None and e.lat is not None and e.lon is not None)
        else None
    )
    return event_to_out(e, distance_km=dist, reason=reason, score=score)
