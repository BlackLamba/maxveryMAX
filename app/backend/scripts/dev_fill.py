"""DEV-ONLY: наполнить локальную БД справочниками и демо-событиями.

НЕ часть продукта: в продукте события пишет только worker/ (инвариант из
app/README.md). Скрипт нужен, чтобы поднять бэкенд локально (SQLite/Postgres)
до того, как будет готов `python -m worker import`.

Использование:
    cd backend
    DATABASE_URL=sqlite+aiosqlite:///./dev.db python scripts/dev_fill.py
    # или просто: python scripts/dev_fill.py  (берёт DATABASE_URL из .env/окружения)

Все записи — data_origin='mock' (в UI — бейдж «Демо-данные»).
Даты генерируются относительно текущего дня (МСК).
"""
from __future__ import annotations

import asyncio
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = os.path.dirname(BACKEND_DIR)
for _p in (APP_ROOT, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from datetime import date, datetime, time, timedelta, timezone  # noqa: E402

from app.db import Base, get_engine, get_session_factory  # noqa: E402
from app.models import CategoryORM, CityORM, EventORM, ProviderORM  # noqa: E402
from shared.categories import CATEGORY_NAMES, CATEGORY_ORDER  # noqa: E402

OFFSET = 3  # все демо-города UTC+3

CITIES = [
    ("moscow", "Москва", 55.7522, 37.6156),
    ("st_petersburg", "Санкт-Петербург", 59.9343, 30.3351),
    ("kazan", "Казань", 55.7963, 49.1088),
    ("sochi", "Сочи", 43.6028, 39.7342),
]


def _local_to_utc(d: date, t: time) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=timezone.utc) - timedelta(
        hours=OFFSET
    )


def build_events(today: date) -> list[dict]:
    def ev(
        title, category, city_slug, day, start, *, end=None, pmin=None, pmax=None,
        free=False, lat=None, lon=None, venue="Демо-площадка", address=None,
        description="Демо-событие (test data)", age=None,
    ):
        c = next(x for x in CITIES if x[0] == city_slug)
        d = today + timedelta(days=day)
        return dict(
            title=title, description=description, category=category,
            city_slug=city_slug, venue=venue, address=address,
            lat=lat if lat is not None else c[2],
            lon=lon if lon is not None else c[3],
            starts=_local_to_utc(d, start),
            ends=_local_to_utc(d, end) if end else None,
            pmin=0 if free else pmin,
            pmax=0 if free else pmax,
            free=free, age=age,
            source_id=f"devfill-{title.lower().replace(' ', '-')}",
        )

    return [
        ev("Джазовый вечер «Синяя луна»", "concert", "moscow", 0, time(19, 0), end=time(22, 0),
           pmin=500, pmax=1200, lat=55.755, lon=37.617, venue="Клуб «Подвал»",
           address="Большая Никитская, 10", description="Квартет джазового стандарта."),
        ev("Выставка «Свет XX века»", "exhibition", "moscow", 0, time(18, 30), end=time(21, 0),
           pmin=500, lat=55.748, lon=37.620, venue="Галерея «Современность»",
           address="Тверская, 7"),
        ev("Лекция «Как планировать личный бюджет»", "lecture", "moscow", 0, time(18, 0),
           end=time(19, 30), free=True, lat=55.760, lon=37.610,
           venue="Библиотека «Прогресс»", address="Пушкинская, 12"),
        ev("Мастер-класс по керамике для начинающих", "master_class", "moscow", 0, time(20, 0),
           end=time(22, 0), free=True, lat=55.770, lon=37.630, venue="Ателье «Глиняное»",
           address="Стрелецкая, 3"),
        ev("Рок-ночь «Напряжение»", "concert", "moscow", 0, time(20, 0), end=time(23, 0),
           pmin=2500, lat=55.870, lon=37.550, venue="Арена «Волна»", age="16+"),
        ev("Спектакль «Чайка»", "theater", "moscow", 1, time(19, 0), end=time(21, 30),
           pmin=1500, pmax=3000, lat=55.742, lon=37.605, venue="МХТ им. Чехова",
           address="Камергерский, 2"),
        ev("Фестиваль уличной еды", "festival", "moscow", 2, time(12, 0), end=time(21, 0),
           free=True, lat=55.731, lon=37.616, venue="Патриаршие пруды"),
        ev("Выставка «Цифровой арт: 10 лет»", "exhibition", "moscow", 7, time(11, 0),
           end=time(20, 0), pmin=700, lat=55.735, lon=37.600, venue="Медиацентр «Вектор»"),
        ev("Детский научный фестиваль", "children", "moscow", 3, time(12, 0), end=time(17, 0),
           pmin=300, pmax=900, lat=55.750, lon=37.622, venue="НЦ «Наукоград»", age="6+"),
        ev("Кинопоказ «Лесные истории»", "cinema", "moscow", 1, time(19, 30), end=time(21, 30),
           pmin=400, pmax=800, lat=55.780, lon=37.590, venue="Кинотеатр «Аврора»"),
        ev("Северное сияние — концерт", "concert", "st_petersburg", 1, time(20, 0),
           pmin=900, venue="Клуб «Фламм»", address="Большой пр. ПС, 50"),
        ev("Выставка «Белые ночи»", "exhibition", "st_petersburg", 0, time(12, 0),
           end=time(20, 0), pmin=350, venue="Эрмитаж-медиа"),
        ev("Кино под открытым небом", "cinema", "kazan", 0, time(21, 0), end=time(23, 0),
           pmin=600, venue="Парк «Чистое озеро»"),
        ev("Лекторий «История Казани»", "lecture", "kazan", 1, time(18, 0),
           end=time(19, 30), free=True, venue="Национальная библиотека"),
        ev("Фестиваль «Город цветов»", "festival", "sochi", 1, time(17, 0), end=time(23, 0),
           free=True, venue="Ривьера", address="Наб. Морская, 1"),
        ev("Джаз на набережной", "concert", "sochi", 3, time(19, 0), end=time(22, 0),
           free=True, venue="Ривьера", address="Наб. Морская, 1"),
        ev("Мастер-класс по сюрфаунгу (теория)", "master_class", "sochi", 5, time(10, 0),
           end=time(13, 0), pmin=1500, pmax=2500, venue="Школа серфинга"),
        ev("Спектакль «Гамлет»", "theater", "st_petersburg", 2, time(19, 0),
           end=time(22, 0), pmin=1200, pmax=4000, venue="БДТ"),
        ev("Кинопремьера «Полночь»", "cinema", "moscow", 4, time(21, 0),
           pmin=700, lat=55.762, lon=37.632, venue="Кинозал «Сатурн»", age="18+"),
        ev("Праздник науки для школьников", "children", "kazan", 6, time(11, 0),
           end=time(16, 0), free=True, venue="Технопарк «Иннополис»"),
    ]


async def main() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    today = (datetime.now(timezone.utc) + timedelta(hours=OFFSET)).date()

    async with factory() as s:
        if (await s.execute(
            CategoryORM.__table__.select().limit(1)
        )).first() is None:
            for i, (slug, name, lat, lon) in enumerate(CITIES, start=1):
                s.add(CityORM(id=i, slug=slug, name=name, lat=lat, lon=lon, tz_offset_hours=3))
            for i, slug in enumerate(CATEGORY_ORDER, start=1):
                s.add(CategoryORM(id=i, slug=slug, name=CATEGORY_NAMES[slug], sort_order=i))
            s.add(ProviderORM(slug="mock", name="Демо-набор"))
            await s.commit()

        # идемпотентность по заголовку: пересоздаём события с текущими датами
        for e in (await s.execute(EventORM.__table__.select())).scalars().all():
            await s.delete(e)
        await s.flush()

        city_ids = {c[0]: i for i, c in enumerate(CITIES, start=1)}
        cat_ids = {slug: i for i, slug in enumerate(CATEGORY_ORDER, start=1)}
        for idx, spec in enumerate(build_events(today), start=1):
            s.add(
                EventORM(
                    id=idx,
                    title=spec["title"],
                    description=spec["description"],
                    category_id=cat_ids[spec["category"]],
                    city_id=city_ids[spec["city_slug"]],
                    provider="mock",
                    venue_name=spec["venue"],
                    address=spec["address"],
                    lat=spec["lat"],
                    lon=spec["lon"],
                    starts_at=spec["starts"],
                    ends_at=spec["ends"],
                    price_min=spec["pmin"],
                    price_max=spec["pmax"],
                    is_free=spec["free"],
                    age_limit=spec["age"],
                    source_url=f"https://example.org/event/{spec['source_id']}",
                    data_origin="mock",
                )
            )
        await s.commit()

    print(f"dev_fill: готово. Демодат: {today} (UTC+3). data_origin=mock")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
