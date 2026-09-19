"""Тестовая инфраструктура: SQLite-БД + демо-набор + HTTP-клиент.

Запуск: cd backend && python -m pytest
БД — отдельный файл .pytest_db/test.db (gitignored), пересоздаётся на каждый прогон.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, time, timedelta, timezone

# Пути: app/ (shared) и backend/ (app)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = os.path.dirname(BACKEND_DIR)
for _p in (APP_ROOT, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_DB_DIR = os.path.join(BACKEND_DIR, ".pytest_db")
os.makedirs(_DB_DIR, exist_ok=True)
_DB_FILE = os.path.join(_DB_DIR, "test.db")
if os.path.exists(_DB_FILE):
    os.remove(_DB_FILE)

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE}"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.db import Base, get_engine, get_session_factory  # noqa: E402
from app.models import CategoryORM, CityORM, EventORM, ProviderORM  # noqa: E402
from shared.categories import CATEGORY_NAMES, CategorySlug, CATEGORY_ORDER  # noqa: E402

OFFSET = 3  # все демо-города UTC+3


def today_local() -> date:
    return (datetime.now(timezone.utc) + timedelta(hours=OFFSET)).date()


def local_to_utc(d: date, t: time) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=timezone.utc) - timedelta(
        hours=OFFSET
    )


CITIES = [
    ("moscow", "Москва", 55.7522, 37.6156),
    ("st_petersburg", "Санкт-Петербург", 59.9343, 30.3351),
    ("kazan", "Казань", 55.7963, 49.1088),
    ("sochi", "Сочи", 43.6028, 39.7342),
]


def _event(
    title: str,
    category: str,
    city_slug: str,
    day_offset: int,
    start: time,
    *,
    end: time | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    is_free: bool = False,
    lat: float | None = None,
    lon: float | None = None,
    venue: str | None = None,
    address: str | None = None,
    description: str = "Тестовое событие",
    age_limit: str | None = None,
) -> dict:
    city = next(c for c in CITIES if c[0] == city_slug)
    d = today_local() + timedelta(days=day_offset)
    starts = local_to_utc(d, start)
    ends = local_to_utc(d, end) if end else None
    source_id = f"mock-{title.lower().replace(' ', '-')}"
    return {
        "title": title,
        "description": description,
        "category_slug": category,
        "city_slug": city_slug,
        "venue_name": venue or "Демо-площадка",
        "address": address,
        "lat": lat if lat is not None else city[2],
        "lon": lon if lon is not None else city[3],
        "starts_at": starts,
        "ends_at": ends,
        "price_min": 0 if is_free else price_min,
        "price_max": 0 if is_free else price_max,
        "is_free": is_free,
        "age_limit": age_limit,
        "source_id": source_id,
        "source_url": f"https://example.org/event/{source_id}",
    }


def _demo_events() -> list[dict]:
    t = today_local()
    return [
        # Москва, сегодня
        _event("Джазовый вечер «Синяя луна»", "concert", "moscow", 0, time(19, 0),
               end=time(22, 0), price_min=500, price_max=1200,
               lat=55.755, lon=37.617, venue="Клуб «Подвал»",
               address="Большая Никитская, 10",
               description="Квартет джазового стандарта с гостем-вокалистом."),
        _event("Выставка «Свет XX века»", "exhibition", "moscow", 0, time(18, 30),
               end=time(21, 0), price_min=500,
               lat=55.748, lon=37.620, venue="Галерея «Современность»",
               address="Тверская, 7"),
        _event("Лекция «Как планировать личный бюджет»", "lecture", "moscow", 0, time(18, 0),
               end=time(19, 30), is_free=True,
               lat=55.760, lon=37.610, venue="Библиотека «Прогресс»",
               address="Пушкинская, 12"),
        _event("Мастер-класс по керамике для начинающих", "master_class", "moscow", 0, time(20, 0),
               end=time(22, 0), is_free=True,
               lat=55.770, lon=37.630, venue="Ателье «Глиняное»",
               address="Стрелецкая, 3"),
        _event("Рок-ночь «Напряжение»", "concert", "moscow", 0, time(20, 0),
               end=time(23, 0), price_min=2500,
               lat=55.870, lon=37.550, venue="Арена «Волна»",
               address="Осташковское шоссе, 35", age_limit="16+"),
        _event("Спектакль «Чайка»", "theater", "moscow", 1, time(19, 0),
               end=time(21, 30), price_min=1500, price_max=3000,
               lat=55.742, lon=37.605, venue="МХТ им. Чехова",
               address="Камергерский, 2"),
        _event("Выставка «Цифровой арт: 10 лет»", "exhibition", "moscow", 7, time(11, 0),
               end=time(20, 0), price_min=700,
               lat=55.735, lon=37.600, venue="Медиацентр «Вектор»",
               address="Воздвиженка, 1"),
        _event("Концерт, который уже прошёл", "concert", "moscow", -3, time(20, 0),
               price_min=800, lat=55.750, lon=37.620, venue="Демо-клуб",
               address="Демо-улица, 1"),
        _event("Детский научный фестиваль", "children", "moscow", 3, time(12, 0),
               end=time(17, 0), price_min=300, price_max=900,
               lat=55.750, lon=37.622, venue="НЦ «Наукоград»",
               address="Профсоюзная, 90", age_limit="6+"),
        # Петербург, Казань, Сочи
        _event("Северное сияние — концерт", "concert", "st_petersburg", 1, time(20, 0),
               price_min=900, venue="Клуб «Фламм»", address="Большой пр. ПС, 50"),
        _event("Кино под открытым небом", "cinema", "kazan", 0, time(21, 0),
               end=time(23, 0), price_min=600, venue="Парк «Чистое озеро»",
               address="ул. Кремлёвская, 1"),
        _event("Фестиваль «Город цветов»", "festival", "sochi", 1, time(17, 0),
               end=time(23, 0), is_free=True, venue="Ривьера", address="Наб. Морская, 1"),
    ]


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as s:
        cities: dict[str, int] = {}
        for i, (slug, name, lat, lon) in enumerate(CITIES, start=1):
            city = CityORM(id=i, slug=slug, name=name, lat=lat, lon=lon, tz_offset_hours=3)
            s.add(city)
            cities[slug] = i
        for i, slug in enumerate(CATEGORY_ORDER, start=1):
            s.add(CategoryORM(id=i, slug=slug, name=CATEGORY_NAMES[slug], sort_order=i))
        s.add(ProviderORM(slug="mock", name="Демо-набор"))
        await s.flush()

        for idx, spec in enumerate(_demo_events(), start=1):
            # id 1..12 стабильны — тесты ссылаются на события по ним
            assert spec["category_slug"] in CATEGORY_ORDER
            s.add(
                EventORM(
                    id=idx,
                    title=spec["title"],
                    description=spec["description"],
                    category_id=int(list(CATEGORY_ORDER).index(spec["category_slug"]) + 1),
                    city_id=cities[spec["city_slug"]],
                    provider="mock",
                    venue_name=spec["venue_name"],
                    address=spec["address"],
                    lat=spec["lat"],
                    lon=spec["lon"],
                    starts_at=spec["starts_at"],
                    ends_at=spec["ends_at"],
                    price_min=spec["price_min"],
                    price_max=spec["price_max"],
                    is_free=spec["is_free"],
                    age_limit=spec["age_limit"],
                    source_url=spec["source_url"],
                    data_origin="mock",
                )
            )
        await s.commit()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def today():
    return today_local()
