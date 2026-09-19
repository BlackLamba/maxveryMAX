"""Единый справочник категорий для Python (бот, бэкенд, воркер).

TS-двойник: shared/categories.ts — значения обязаны совпадать 1-в-1.
Добавление категории = правка обоих файлов в одном коммите + уведомление команды.
"""
from __future__ import annotations

from enum import Enum


class CategorySlug(str, Enum):
    """Слуги категорий — устойчивые ключи для API и deep link."""

    CONCERT = "concert"
    EXHIBITION = "exhibition"
    THEATER = "theater"
    LECTURE = "lecture"
    MASTER_CLASS = "master_class"
    FESTIVAL = "festival"
    CINEMA = "cinema"
    CHILDREN = "children"


#: Человекочитаемые названия (для кнопок бота и карточек).
CATEGORY_NAMES: dict[str, str] = {
    "concert": "Концерт",
    "exhibition": "Выставка",
    "theater": "Театр",
    "lecture": "Лекция",
    "master_class": "Мастер-класс",
    "festival": "Фестиваль",
    "cinema": "Кино",
    "children": "Детям",
}

#: Порядок по умолчанию для кнопок бота (шаг «что интересует?»).
CATEGORY_ORDER: tuple[str, ...] = (
    "concert",
    "theater",
    "exhibition",
    "lecture",
    "master_class",
    "festival",
    "cinema",
    "children",
)


def category_name(slug: str) -> str:
    """Название по слугу; неизвестный слуг возвращается как есть."""
    return CATEGORY_NAMES.get(slug, slug)
