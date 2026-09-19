"""POST /api/search и POST /api/search/natural."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..repositories import references_repo
from ..schemas.common import Envelope
from ..schemas.events import EventFilters, EventOut, NaturalIn, NaturalOut
from ..services import events_service
from ..services.natural import parse_natural
from ..services.timeutils import today_local

router = APIRouter(tags=["search"])

#: Точка-заглушка для «рядом», если координат пользователя нет: центр Москвы.
FALLBACK_POINT = (55.7522, 37.6156)


@router.post("/search", response_model=Envelope[EventOut])
async def search(body: EventFilters, db: AsyncSession = Depends(get_db)) -> Envelope[EventOut]:
    """Упрощённый поиск: те же фильтры, что у GET /api/events, но в body."""
    return await events_service.search_events(db, body)


@router.post("/search/natural", response_model=NaturalOut)
async def search_natural(body: NaturalIn, db: AsyncSession = Depends(get_db)) -> NaturalOut:
    """Фраза пользователя → фильтры → результаты (Could Have)."""
    offset_hours = get_settings().default_tz_offset_hours
    f, understood, city_slug = parse_natural(body.query, today_local(offset_hours))

    if city_slug:
        city_id = await references_repo.city_id_by_slug(db, city_slug)
        if city_id is not None:
            f.city_id = city_id
    if body.city_id is not None:
        f.city_id = body.city_id

    # «рядом» без координат пользователя — от центра города (демо-упрощение).
    if f.radius_km is not None and f.lat is None:
        city = (
            await references_repo.city_by_id(db, f.city_id)
            if f.city_id is not None
            else None
        )
        if city is not None and city.lat is not None and city.lon is not None:
            f.lat, f.lon = city.lat, city.lon
        else:
            f.lat, f.lon = FALLBACK_POINT
        understood.append("точка — центр города")

    if not understood:
        return NaturalOut(
            filters=f.model_dump(mode="json"),
            understood=[],
            items=[],
            total=0,
            hint="Не удалось распознать ограничения — попробуйте, например: "
            "«концерт сегодня вечером до 1500 рублей»",
        )

    result = await events_service.search_events(db, f)
    return NaturalOut(
        filters=f.model_dump(mode="json"),
        understood=understood,
        items=result.items,
        total=result.total,
        hint=result.hint,
    )
