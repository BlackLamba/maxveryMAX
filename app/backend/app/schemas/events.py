"""Схемы домена событий: фильтры поиска, карточка EventOut, справочники."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.categories import CategorySlug

SortOption = Literal["relevance", "date_asc", "price_asc", "price_desc", "distance"]


class EventFilters(BaseModel):
    """Параметры поиска.

    Используются и как query (GET /api/events — через Depends),
    и как body (POST /api/search). Semантика — docs/10_backend_design.md, п. 4.3.
    """

    city_id: Optional[int] = Field(None, ge=1)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    time_from: Optional[time] = None
    time_to: Optional[time] = None
    category: Optional[list[CategorySlug]] = None
    price_max: Optional[int] = Field(None, ge=0)
    is_free: Optional[bool] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, gt=0, le=200)
    sort: SortOption = "relevance"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    #: Необязательно: uid из MAX для подтягивания сохранённых предпочтений.
    user_id: Optional[str] = Field(None, max_length=128)

    @model_validator(mode="after")
    def _check_consistency(self) -> "EventFilters":
        if self.date_from and self.date_to and self.date_to < self.date_from:
            raise ValueError("date_to раньше date_from")
        if self.radius_km is not None and (self.lat is None or self.lon is None):
            raise ValueError("radius_km требует lat и lon")
        if self.sort == "distance" and (self.lat is None or self.lon is None):
            raise ValueError("sort=distance требует lat и lon")
        # Временное окно имеет смысл для одного дня (диалог бота всегда даёт дату).
        if (self.time_from is not None or self.time_to is not None) and not (
            self.date_from is not None and self.date_from == self.date_to
        ):
            raise ValueError(
                "временное окно (time_from/time_to) задаётся для одного дня: "
                "укажите date_from = date_to"
            )
        return self


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class EventOut(BaseModel):
    """Карточка события для интерфейсов (+ «почему подходит»)."""

    id: int
    title: str
    description: str
    category: str
    category_name: str
    city_id: int
    city_slug: str
    city_name: str
    venue_name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_km: Optional[float] = None  # только когда у пользователя есть координаты
    starts_at: datetime
    ends_at: Optional[datetime] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    is_free: bool
    price_display: str
    age_limit: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    provider: str
    data_origin: str  # mock|live — mock обязан показываться как «Демо-данные»
    quality_score: int = 0
    updated_at: datetime
    reason: Optional[str] = None  # «почему подходит»
    score: Optional[float] = None  # балл ранжирования (прозрачность, на UI не обязателен)


class NaturalIn(BaseModel):
    """POST /api/search/natural — фраза пользователя (Could Have)."""

    query: str = Field(min_length=1, max_length=300)
    city_id: Optional[int] = Field(None, ge=1)


class NaturalOut(BaseModel):
    filters: dict  # EventFilters в JSON — мини-апп может показать применённые чипы
    understood: list[str]  # что парсер понял из фразы
    items: list[EventOut]
    total: int
    hint: Optional[str] = None
