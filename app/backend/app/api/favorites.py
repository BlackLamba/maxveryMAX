"""Избранное: POST /api/favorites, GET /api/favorites, DELETE /api/favorites/{event_id}."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..errors import ApiNotFound
from ..models import ACTION_FAV_ADD, ACTION_FAV_REMOVE
from ..repositories import events_repo, user_repo
from ..schemas.common import Envelope
from ..schemas.events import EventOut
from ..schemas.user import FavoriteIn, FavoriteOut
from ..services import events_service

router = APIRouter(tags=["favorites"])


@router.post("/favorites", status_code=201)
async def add_favorite(body: FavoriteIn, db: AsyncSession = Depends(get_db)) -> dict:
    event = await events_repo.get(db, body.event_id)
    if event is None:
        raise ApiNotFound(f"событие {body.event_id} не найдено")
    await user_repo.add_favorite(db, body.user_id, body.event_id)
    await user_repo.log_interaction(db, body.user_id, body.event_id, ACTION_FAV_ADD)
    await db.commit()
    return {"ok": True}


@router.get("/favorites", response_model=Envelope[FavoriteOut])
async def list_favorites(
    user_id: str = Query(min_length=1, max_length=128),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> Envelope[FavoriteOut]:
    rows, total = await user_repo.list_favorites(db, user_id, limit, offset)
    items = [
        FavoriteOut(**events_service.event_to_out(event).model_dump(), added_at=fav.added_at)
        for fav, event in rows
    ]
    return Envelope(items=items, total=total)


@router.delete("/favorites/{event_id}")
async def remove_favorite(
    event_id: int,
    user_id: str = Query(min_length=1, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> dict:
    removed = await user_repo.remove_favorite(db, user_id, event_id)
    if not removed:
        raise ApiNotFound("нет такого события в избранном")
    await user_repo.log_interaction(db, user_id, event_id, ACTION_FAV_REMOVE)
    await db.commit()
    return {"ok": True}
