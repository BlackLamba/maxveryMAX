"""Общие Pydantic-модели: единая модель события и фильтров.

Используют: worker/ (нормализация raw → Event), backend/ (контракт API),
bot/ (сбор параметров и deep link). Здесь НЕ должно быть бизнес-логики,
запросов к БД и HTTP-зависимостей (app/README.md, раздел 5.5).
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .categories import CategorySlug

DataOrigin = Literal["mock", "live"]
EventStatus = Literal["active", "sold_out", "cancelled"]


class City(BaseModel):
    id: Optional[int] = None
    slug: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    #: Смещение локального времени города от UTC (MVP: все демо-города +3).
    tz_offset_hours: int = 3


class Category(BaseModel):
    id: Optional[int] = None
    slug: CategorySlug
    name: str


class Event(BaseModel):
    """Событие в нормализованном виде: воркер пишет, backend читает.

    `source` + `source_id` — ключ идемпотентного upsert `(source, source_id)`.
    `data_origin='mock'` обязан быть явно виден интерфейсу (бейдж «Демо-данные»).
    """

    id: Optional[int] = None
    title: str
    description: str = ""
    category: CategorySlug
    city_slug: str
    provider: str = "mock"  # slug провайдера: mock/timepad/kudago/culture
    venue_name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    starts_at: datetime  # timezone-aware (UTC в БД)
    ends_at: Optional[datetime] = None
    #: Рубли. price_min=None — цена неизвестна; бесплатное событие: is_free=True, price_min=0.
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    is_free: bool = False
    age_limit: Optional[str] = None  # например "12+"
    image_url: Optional[str] = None
    source: str = "mock"
    source_id: str
    source_url: Optional[str] = None  # официальный источник (афиша/билетный оператор)
    data_origin: DataOrigin = "mock"
    tags: list[str] = Field(default_factory=list)
    status: EventStatus = "active"


class FilterParams(BaseModel):
    """Единые параметры поиска: deep link бота → GET /api/events → мини-апп.

    Соответствует контракту backend (docs/10_backend_design.md, раздел 4.3).
    """

    city_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    time_from: Optional[time] = None
    time_to: Optional[time] = None
    category: Optional[list[CategorySlug]] = None
    price_max: Optional[int] = Field(None, ge=0)
    is_free: Optional[bool] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = Field(None, gt=0, le=200)
    sort: Literal["relevance", "date_asc", "price_asc", "price_desc", "distance"] = "relevance"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
