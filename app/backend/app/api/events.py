"""GET /api/events, GET /api/events/{id}, POST /api/events/{id}/click."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from shared.categories import CategorySlug
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..schemas.common import Envelope
from ..schemas.events import EventFilters, EventOut
from ..schemas.user import ClickIn
from ..services import events_service, clicks

router = APIRouter(tags=["events"])


@router.get("/events", response_model=Envelope[EventOut])
async def list_events(
    # Модель-класс как зависимость: FastAPI заполняет её поля из query-параметров.
    # Ошибки валидации (вкл. model_validator) → 400: handler pydantic.ValidationError
    # в errors.py (FastAPI не оборачивает их в RequestValidationError для Depends-моделей).
    filters: Annotated[EventFilters, Depends()],
    # list-поля в Depends-моделях этот FastAPI молча игнорирует (checked: 0.141),
    # поэтому категория идёт явным query-параметром: ?category=concert&category=theater
    # или ?category=concert,theater
    category: Annotated[
        Optional[list[CategorySlug]],
        Query(description="категории (повторяемый параметр или через запятую)"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> Envelope[EventOut]:
    """Поиск событий с фильтрами и ранжированием (+ reason «почему подходит»)."""
    if category is not None:
        filters.category = category
    return await events_service.search_events(db, filters)


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    filters: Annotated[EventFilters, Depends()],
    category: Annotated[Optional[list[CategorySlug]], Query()] = None,
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Карточка события. Необязательные фильтры в query влияют только на reason."""
    if category is not None:
        filters.category = category
    return await events_service.event_detail(db, event_id, filters)


@router.post("/events/{event_id}/click", status_code=201)
async def click_source(
    event_id: int,
    body: ClickIn,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Лог перехода пользователя на официальный источник (метрика пилота)."""
    await clicks.log_click(db, event_id, body.user_id, body.meta)
    return {"ok": True}
