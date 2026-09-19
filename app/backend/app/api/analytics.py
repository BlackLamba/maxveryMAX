"""Мини-аналитика для метрик пилота (08): GET /api/analytics/summary."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..repositories import user_repo
from ..schemas.user import AnalyticsOut

router = APIRouter(tags=["analytics"])


@router.get("/analytics/summary", response_model=AnalyticsOut)
async def summary(
    user_id: str = Query(min_length=1, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOut:
    data = await user_repo.interactions_summary(db, user_id)
    return AnalyticsOut(**data)
