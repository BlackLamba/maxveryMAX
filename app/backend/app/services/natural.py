"""Простой парсер фразы пользователя → фильтры (Could Have, 05_MVP.md п. 5).

Без ML: ключевые слова + regex. Пример:
  «концерт сегодня вечером до 1500₽ рядом»
  → category=[concert], date=today, time 17:00–23:00, price_max=1500, radius 5 км.
"""
from __future__ import annotations

import re
from datetime import date, time, timedelta

from shared.categories import CATEGORY_NAMES, CategorySlug

from ..schemas.events import EventFilters

# Префиксные стеми категорий (совпадение с началом слова, «?<!\w» перед словом).
CATEGORY_STEMS: dict[str, tuple[str, ...]] = {
    "concert": ("концерт", "музык", "джаз", "оркестр", "симфонич", "сольный"),
    "exhibition": ("выставк", "галере", "искусств"),
    "theater": ("театр", "спектакл", "мюзикл", "опер", "балет", "пьес"),
    "lecture": ("лекци", "вебинар", "доклад", "семинар"),
    "master_class": ("мастер-класс", "мастеркласс", "воркшоп"),
    "festival": ("фестивал",),
    "cinema": ("кино", "фильм", "премьер"),
    "children": ("детск", "для детей", "детям", "с детьми"),
}
# Ключи, которые должны стоять отдельным словом (иначе «арт» попадёт в «картинг»).
CATEGORY_WORD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "concert": ("рок",),
    "exhibition": ("арт", "фото"),
}

DATE_OFFSETS: tuple[tuple[str, int], ...] = (("послезавтра", 2), ("завтра", 1), ("сегодня", 0))
WEEKDAY_STEMS: tuple[tuple[str, int, str], ...] = (
    ("понедельник", 0, "в понедельник"),
    ("вторник", 1, "во вторник"),
    ("сред", 2, "в среду"),
    ("четверг", 3, "в четверг"),
    ("пятниц", 4, "в пятницу"),
    ("суббат", 5, "в субботу"),
    ("воскрес", 6, "в воскресенье"),
)
# Порядок важен: «сегодня» содержит «дн», поэтому время ищем по началу слова.
TIME_STEMS: tuple[tuple[str, time, time], ...] = (
    ("вечер", time(17, 0), time(23, 0)),
    ("ноч", time(22, 0), time(23, 59)),
    ("утр", time(8, 0), time(12, 0)),
    ("дн", time(12, 0), time(17, 0)),
)
RADIUS_STEMS: tuple[tuple[str, int], ...] = (("не далеко", 10), ("недалеко", 10), ("рядом", 5))
CITY_STEMS: tuple[tuple[str, str], ...] = (
    ("москв", "moscow"),
    ("петербург", "st_petersburg"),
    ("питер", "st_petersburg"),
    ("казан", "kazan"),
    ("сочи", "sochi"),
)

TIME_RANGE_RE = re.compile(r"(\d{1,2})[:.](\d{2})\s*(?:до|—|–|-)\s*(\d{1,2})[:.](\d{2})")
TIME_FROM_RE = re.compile(r"\bс\s+(\d{1,2})[:.](\d{2})\b")
PRICE_RE = re.compile(r"до\s+([\d\s]{1,9})\s*(?:руб\.?|₽|р\.)?")


def _has_stem(q: str, stem: str) -> bool:
    """Совпадение с началом слова: (?<!\w) перед словом (защита от «сегодня»→«дн»)."""
    return re.search(rf"(?<!\w){re.escape(stem)}", q) is not None


def _has_word(q: str, word: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", q) is not None


def parse_natural(query: str, today: date) -> tuple[EventFilters, list[str], str | None]:
    """Возвращает (filters, understood, city_slug|None)."""
    q = query.lower()
    f = EventFilters()
    understood: list[str] = []
    city_slug: str | None = None

    # --- время ---------------------------------------------------------------
    m = TIME_RANGE_RE.search(q)
    if m:
        f.time_from = time(int(m.group(1)), int(m.group(2)))
        f.time_to = time(int(m.group(3)), int(m.group(4)))
        understood.append(f"с {f.time_from:%H:%M} до {f.time_to:%H:%M}")
    else:
        m = TIME_FROM_RE.search(q)
        if m:
            f.time_from = time(int(m.group(1)), int(m.group(2)))
            understood.append(f"с {f.time_from:%H:%M}")
        else:
            for stem, tf, tt in TIME_STEMS:
                if _has_stem(q, stem):
                    f.time_from, f.time_to = tf, tt
                    understood.append(f"{tf:%H:%M}–{tt:%H:%M} (время суток)")
                    break

    # --- дата ----------------------------------------------------------------
    for word, delta in DATE_OFFSETS:
        if _has_word(q, word):
            d = today + timedelta(days=delta)
            f.date_from = f.date_to = d
            understood.append(word)
            break
    if f.date_from is None and _has_stem(q, "выходны"):
        wd = today.weekday()
        if wd == 6:  # воскресенье — выходные продолжаются сегодня
            f.date_from = f.date_to = today
        else:
            sat = today + timedelta(days=(5 - wd) % 7 or 7)
            f.date_from, f.date_to = sat, sat + timedelta(days=1)
        understood.append("на выходных")
    if f.date_from is None:
        for stem, wd, label in WEEKDAY_STEMS:
            if _has_stem(q, stem):
                f.date_from = f.date_to = today + timedelta(days=(wd - today.weekday()) % 7)
                understood.append(label)
                break

    # «вечером» без даты — по смыслу «сегодня»
    if (f.time_from is not None or f.time_to is not None) and f.date_from is None:
        f.date_from = f.date_to = today
        understood.append("сегодня (по времени)")

    # --- категория -------------------------------------------------------------
    for slug, stems in CATEGORY_STEMS.items():
        hit = any(_has_stem(q, s) for s in stems)
        hit = hit or any(_has_word(q, w) for w in CATEGORY_WORD_KEYWORDS.get(slug, ()))
        if hit:
            f.category = [CategorySlug(slug)]
            understood.append(CATEGORY_NAMES[slug].lower())
            break

    # --- цена ------------------------------------------------------------------
    if _has_stem(q, "бесплатн"):
        f.is_free = True
        understood.append("бесплатно")
    m = PRICE_RE.search(q)
    if m and f.is_free is not True:
        value = int(re.sub(r"\D", "", m.group(1)))
        if value > 0:
            f.price_max = value
            understood.append(f"до {value} ₽")

    # --- расстояние --------------------------------------------------------------
    # Координаты здесь не ставим: точка берётся в роутере (город из фразы/параметра,
    # иначе центр города по умолчанию). radius_km без lat/lon — 400 по контракту.
    for stem, km in RADIUS_STEMS:
        if stem in q:
            f.radius_km = float(km)
            understood.append(f"рядом (до {km} км)")
            break

    # --- город -------------------------------------------------------------------
    for stem, slug in CITY_STEMS:
        if _has_stem(q, stem):
            city_slug = slug
            understood.append(slug)
            break

    return f, understood, city_slug
