"""Простое балльное ранжирование + объяснение «почему подходит».

Веса — часть проектной гипотезы (05_MVP.md, п. 3.1) и настраиваются после
пользовательского тестирования. Жёсткие фильтры (город/дата/категория/цена/
радиус) уже выполнены в SQL — здесь только порядок и объяснение.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

MAX_SCORE = 100.0

W_TIME = 25.0
W_PRICE = 25.0
W_DISTANCE = 25.0
W_PREF = 10.0
W_FRESH = 10.0

NEUTRAL_TIME = 12.0
NEUTRAL_PRICE = 12.0
NEUTRAL_DISTANCE = 8.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _local_date(dt: datetime, offset_hours: int) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt + timedelta(hours=offset_hours)).date()


def _ensure_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


@dataclass(slots=True)
class RankContext:
    """Эффективные параметры, по которым считаются баллы."""

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    window_start: Optional[datetime] = None  # UTC
    window_end: Optional[datetime] = None  # UTC
    price_max: Optional[int] = None
    is_free: Optional[bool] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = None
    pref_categories: frozenset[str] = frozenset()
    tz_offset_hours: int = 3
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def evaluate(event, cat_slug: str, ctx: RankContext) -> tuple[float, str]:
    """Возвращает (score 0..100, reason «почему подходит»).

    `event` — EventORM: нужны starts_at, price_min, is_free, lat, lon,
    data_origin, updated_at.
    """
    score = 0.0
    frags: list[str] = []
    start_utc = _ensure_utc(event.starts_at)

    # 1) Время ---------------------------------------------------------------
    if ctx.window_start is not None and ctx.window_end is not None:
        if ctx.window_start <= start_utc <= ctx.window_end:
            score += W_TIME
            start_hm = (start_utc + timedelta(hours=ctx.tz_offset_hours)).strftime("%H:%M")
            frags.append(f"начало в {start_hm} — в ваше время")
        elif ctx.date_from is not None and _local_date(start_utc, ctx.tz_offset_hours) == ctx.date_from:
            score += 10.0
            frags.append(f"в ваш день ({ctx.date_from:%d.%m})")
    elif ctx.date_from is not None:
        if _local_date(start_utc, ctx.tz_offset_hours) == ctx.date_from:
            score += 15.0
            frags.append(f"в ваш день ({ctx.date_from:%d.%m})")
        else:
            score += 5.0
    else:
        score += NEUTRAL_TIME

    # 2) Цена ----------------------------------------------------------------
    if ctx.is_free:
        score += W_PRICE
        frags.append("бесплатно")
    elif ctx.price_max is not None:
        if event.is_free:
            score += W_PRICE
            frags.append("бесплатно — укладывается в бюджет")
        elif event.price_min is not None and event.price_min <= ctx.price_max:
            score += W_PRICE
            frags.append(f"вписывается в бюджет (от {event.price_min} ₽ ≤ {ctx.price_max} ₽)")
        # price_min is None — цена неизвестна: событие прошло фильтр, баллы не начисляем
    else:
        score += NEUTRAL_PRICE

    # 3) Расстояние ----------------------------------------------------------
    if (
        ctx.lat is not None
        and ctx.lon is not None
        and event.lat is not None
        and event.lon is not None
    ):
        d = haversine_km(ctx.lat, ctx.lon, event.lat, event.lon)
        ref = ctx.radius_km or 15.0
        score += W_DISTANCE * max(0.0, 1.0 - d / max(ref, 1.0))
        if d <= 3.0:
            frags.append(f"рядом ({d:.1f} км)")
        elif d <= ref:
            frags.append(f"в пределах вашего радиуса ({d:.1f} км)")
    else:
        score += NEUTRAL_DISTANCE

    # 4) Сохранённые интересы (мягкий бонус) ---------------------------------
    if ctx.pref_categories and cat_slug in ctx.pref_categories:
        score += W_PREF
        frags.append("совпадает с вашими сохранёнными интересами")
    else:
        score += W_PREF / 2.0

    # 5) Свежесть данных (только баллы, не попадает в reason) ----------------
    if event.data_origin == "live":
        score += 5.0
    else:
        score += 2.0
    updated = event.updated_at
    if updated is not None:
        updated = _ensure_utc(updated)
        if (ctx.now - updated).total_seconds() < 7 * 86400:
            score += 3.0
    if 0 <= (start_utc - ctx.now).total_seconds() <= 7 * 86400:
        score += 2.0

    score = min(score, MAX_SCORE)
    reason = "; ".join(frags) if frags else "найдено по вашим фильтрам"
    return score, reason
