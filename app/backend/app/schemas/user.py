"""Схемы пользователя: избранное, предпочтения, клики, аналитика."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from shared.categories import CategorySlug

from .events import EventOut


class ClickIn(BaseModel):
    """POST /api/events/{id}/click — переход пользователя на официальный источник."""

    user_id: Optional[str] = Field(None, max_length=128)
    meta: Optional[dict] = None


class FavoriteIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    event_id: int = Field(ge=1)


class FavoriteOut(EventOut):
    added_at: datetime


class PreferenceIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    categories: list[CategorySlug] = Field(default_factory=list)
    price_max: Optional[int] = Field(None, ge=0)
    radius_km: Optional[float] = Field(None, gt=0, le=200)


class PreferenceOut(BaseModel):
    user_id: str
    categories: list[str] = Field(default_factory=list)
    price_max: Optional[int] = None
    radius_km: Optional[float] = None
    saved: bool = False
    updated_at: Optional[datetime] = None


class AnalyticsOut(BaseModel):
    """Мини-сводка по пользователю — для метрик пилота (08)."""

    user_id: str
    clicks_to_source: int = 0
    favorites: int = 0
    top_categories: dict[str, int] = Field(default_factory=dict)
