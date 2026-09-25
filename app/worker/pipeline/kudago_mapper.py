"""Маппинг слагов KudaGo → наши slug'и (categories, cities).

Источник категорий: https://kudago.com/public-api/v1.4/event-categories/
Источник локаций:   https://kudago.com/public-api/v1.4/locations/
"""
from __future__ import annotations

from shared.categories import CategorySlug

#: KudaGo category slug → наш CategorySlug.
#: События с категориями вне этого словаря пропускаются.
KUDAGo_CATEGORY_MAP: dict[str, CategorySlug] = {
    "concert": CategorySlug.CONCERT,
    "exhibition": CategorySlug.EXHIBITION,
    "theater": CategorySlug.THEATER,
    "education": CategorySlug.LECTURE,
    "festival": CategorySlug.FESTIVAL,
    "holiday": CategorySlug.FESTIVAL,
    "kids": CategorySlug.CHILDREN,
    "cinema": CategorySlug.CINEMA,
    # остальные (entertainment, party, quest, tour, other) — пропускаем
}

#: KudaGo location slug → наш city_slug (совпадает с cities.slug в БД).
KUDAGo_CITY_MAP: dict[str, str] = {
    "msk": "moscow",
    "spb": "spb",
    "kzn": "kazan",
    "nsk": "novosibirsk",
    "ekb": "ekaterinburg",
    "nnv": "nizhny-novgorod",
    "krd": "krasnodar",
    "sochi": "sochi",
    "ufa": "ufa",
    "smr": "samara",
    "vbg": "vyborg",
    "krasnoyarsk": "krasnoyarsk",
}


def map_category(kudago_slugs: list[str]) -> CategorySlug | None:
    """Берём первую известную категорию. Нет подходящей → None (событие пропускается)."""
    for slug in kudago_slugs:
        cat = KUDAGo_CATEGORY_MAP.get(slug)
        if cat is not None:
            return cat
    return None


def map_city(kudago_location: str) -> str | None:
    return KUDAGo_CITY_MAP.get(kudago_location)