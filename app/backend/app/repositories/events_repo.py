"""Запросы к каталогу событий: фильтрация, сортировка, вспомогательные для hint."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CategoryORM, EventORM
from ..schemas.events import EventFilters

EARTH_RADIUS_KM = 6371.0
_MAX_PRICE_SENTINEL = 10**9


def _effective_price():
    """Эффективная цена для сортировок/hint: 0 — бесплатно, иначе price_min.

    Цена неизвестна (price_min IS NULL) → sentinel: такие события уходят в конец
    сортировки по цене.
    """
    return case(
        (EventORM.is_free.is_(True), 0),
        else_=func.coalesce(EventORM.price_min, _MAX_PRICE_SENTINEL),
    ).label("effective_price")


def _distance_km_expr(lat: float, lon: float):
    """Haversine в SQL (работает и в PostgreSQL, и в SQLite ≥3.35)."""
    lat1 = func.radians(lat)
    lat2 = func.radians(EventORM.lat)
    dlat = func.radians(EventORM.lat - lat) / 2
    dlon = func.radians(EventORM.lon - lon) / 2
    sin_dlat = func.sin(dlat)
    sin_dlon = func.sin(dlon)
    a = sin_dlat * sin_dlat + func.cos(lat1) * func.cos(lat2) * sin_dlon * sin_dlon
    return EARTH_RADIUS_KM * 2 * func.asin(func.sqrt(a))


def _where(
    f: EventFilters,
    bounds: Optional[tuple[datetime, datetime]],
    *,
    ignore_price: bool = False,
    ignore_category: bool = False,
    ignore_distance: bool = False,
) -> list:
    conds = [EventORM.status == "active"]
    if f.city_id is not None:
        conds.append(EventORM.city_id == f.city_id)
    if not ignore_category and f.category:
        slugs = [c.value for c in f.category]
        conds.append(EventORM.category_id.in_(
            select(CategoryORM.id).where(CategoryORM.slug.in_(slugs))
        ))
    if not ignore_price:
        if f.price_max is not None:
            conds.append(
                or_(
                    EventORM.is_free.is_(True),
                    EventORM.price_min.is_(None),
                    EventORM.price_min <= f.price_max,
                )
            )
        if f.is_free:
            conds.append(EventORM.is_free.is_(True))
    if bounds is not None:
        start, end = bounds
        conds.append(EventORM.starts_at >= start)
        conds.append(EventORM.starts_at <= end)
    if not ignore_distance and f.lat is not None and f.lon is not None:
        conds.append(EventORM.lat.is_not(None))
        conds.append(EventORM.lon.is_not(None))
        if f.radius_km is not None:
            conds.append(_distance_km_expr(f.lat, f.lon) <= f.radius_km)
    return conds


def _base_stmt():
    # category/city подгружаются через lazy="joined" (см. models/event.py).
    return select(EventORM)


def _order(f: EventFilters, max_candidates: int) -> tuple[list, int, int]:
    if f.sort == "date_asc":
        return [EventORM.starts_at.asc()], f.offset, f.limit
    if f.sort == "price_asc":
        return [_effective_price().asc(), EventORM.starts_at.asc()], f.offset, f.limit
    if f.sort == "price_desc":
        return [_effective_price().desc(), EventORM.starts_at.asc()], f.offset, f.limit
    if f.sort == "distance":
        return [_distance_km_expr(f.lat, f.lon).asc()], f.offset, f.limit
    # relevance: берём пул кандидатов, баллы считает ranking.py
    return [EventORM.starts_at.asc()], 0, max_candidates


async def fetch(
    db: AsyncSession,
    f: EventFilters,
    bounds: Optional[tuple[datetime, datetime]],
    *,
    max_candidates: int = 500,
) -> list[EventORM]:
    stmt = _base_stmt().where(*_where(f, bounds))
    order, offset, limit = _order(f, max_candidates)
    stmt = stmt.order_by(*order).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count(db: AsyncSession, f: EventFilters, bounds: Optional[tuple[datetime, datetime]]) -> int:
    stmt = select(func.count()).select_from(EventORM).where(*_where(f, bounds))
    return int((await db.execute(stmt)).scalar_one())


async def get(db: AsyncSession, event_id: int) -> Optional[EventORM]:
    result = await db.execute(_base_stmt().where(EventORM.id == event_id))
    return result.scalar_one_or_none()


async def min_price(
    db: AsyncSession,
    f: EventFilters,
    bounds: Optional[tuple[datetime, datetime]],
) -> Optional[int]:
    """Самая низкая цена при тех же условиях, но без ограничения по цене (для hint)."""
    stmt = (
        select(func.min(_effective_price()))
        .select_from(EventORM)
        .where(*_where(f, bounds, ignore_price=True))
    )
    value = (await db.execute(stmt)).scalar_one()
    if value is None or value >= _MAX_PRICE_SENTINEL:
        return None
    return int(value)


async def available_categories(
    db: AsyncSession,
    f: EventFilters,
    bounds: Optional[tuple[datetime, datetime]],
) -> list[str]:
    """Какие категории реально есть в заданных условиях (для hint)."""
    stmt = (
        select(CategoryORM.slug)
        .join(EventORM, EventORM.category_id == CategoryORM.id)
        .where(*_where(f, bounds, ignore_price=True, ignore_category=True))
        .distinct()
    )
    result = await db.execute(stmt)
    return [row for row in result.scalars().all() if row]


async def nearest_event_date(
    db: AsyncSession,
    f: EventFilters,
    from_utc: datetime,
    horizon_days: int = 30,
) -> Optional[date]:
    """Ближайшее событие при тех же условиях, но без ограничения по дате (для hint)."""
    window = (from_utc, from_utc + timedelta(days=horizon_days))
    stmt = (
        select(func.min(EventORM.starts_at))
        .select_from(EventORM)
        .where(*_where(f, window, ignore_price=True))
    )
    value = (await db.execute(stmt)).scalar_one()
    return value.date() if value is not None else None
