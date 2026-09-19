"""Перевод локальных дат/окон в UTC-границы для SQL.

MVP: оффсет берётся из cities.tz_offset_hours (все демо-города +3) либо из
default_tz_offset_hours, если город не задан.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


def today_local(offset_hours: int) -> date:
    """Сегодняшняя локальная дата при заданном оффсете от UTC."""
    return (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).date()


def local_dt_to_utc(d: date, t: time, offset_hours: int) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=timezone.utc) - timedelta(
        hours=offset_hours
    )


def window_utc_bounds(
    d: date, time_from: time | None, time_to: time | None, offset_hours: int
) -> tuple[datetime, datetime]:
    """UTC-границы временного окна одного дня. Окно через полночь (22:00–01:00) поддерживается."""
    tf = time_from or time(0, 0)
    tt = time_to or time(23, 59)
    start = local_dt_to_utc(d, tf, offset_hours)
    end = local_dt_to_utc(d, tt, offset_hours)
    if end <= start:
        end = local_dt_to_utc(d + timedelta(days=1), tt, offset_hours)
    return start, end


def date_range_utc(date_from: date, date_to: date, offset_hours: int) -> tuple[datetime, datetime]:
    """UTC-границы диапазона дат (локальные сутки включительно)."""
    start = local_dt_to_utc(date_from, time(0, 0), offset_hours)
    end = local_dt_to_utc(date_to, time(23, 59), offset_hours) + timedelta(seconds=59)
    return start, end
