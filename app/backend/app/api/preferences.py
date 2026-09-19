"""Сохранённые предпочтения: POST /api/preferences, GET /api/preferences."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import UserPreferencesORM
from ..repositories import user_repo
from ..schemas.user import PreferenceIn, PreferenceOut

router = APIRouter(tags=["preferences"])


def _to_out(user_id: str, prefs: UserPreferencesORM, saved: bool) -> PreferenceOut:
    return PreferenceOut(
        user_id=user_id,
        categories=list(prefs.categories or []),
        price_max=prefs.price_max,
        radius_km=prefs.radius_km,
        saved=saved,
        updated_at=prefs.updated_at,
    )


@router.post("/preferences", status_code=201, response_model=PreferenceOut)
async def save_preferences(body: PreferenceIn, db: AsyncSession = Depends(get_db)) -> PreferenceOut:
    prefs = await user_repo.upsert_preferences(
        db,
        body.user_id,
        [c.value for c in body.categories],
        body.price_max,
        body.radius_km,
    )
    await db.commit()
    return _to_out(body.user_id, prefs, saved=True)


@router.get("/preferences", response_model=PreferenceOut)
async def get_preferences(
    user_id: str = Query(min_length=1, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> PreferenceOut:
    prefs = await user_repo.get_preferences(db, user_id)
    if prefs is None:
        return PreferenceOut(user_id=user_id, saved=False)
    return _to_out(user_id, prefs, saved=True)
