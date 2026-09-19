from __future__ import annotations

from datetime import timedelta

from rapidfuzz import fuzz

from shared.models import Event  # type: ignore[import-not-found]

#: Веса адаптированы под доступные поля (нет organizer-поля).
W_TITLE = 0.40
W_TIME = 0.35
W_PLACE = 0.25
THRESHOLD = 0.85


def _similarity(a: Event, b: Event) -> float:
    if a.city_slug != b.city_slug:
        return 0.0
    title = fuzz.token_set_ratio(a.title, b.title) / 100.0
    dt = abs((a.starts_at - b.starts_at).total_seconds())
    time = 1.0 if dt <= timedelta(hours=2).total_seconds() else max(0.0, 1.0 - dt / 86400)
    place = 1.0 if (a.venue_name and a.venue_name == b.venue_name) else 0.0
    return W_TITLE * title + W_TIME * time + W_PLACE * place


def deduplicate(events: list[Event]) -> list[list[Event]]:
    """Группирует похожие события. Первый элемент группы — «ведущий»,
    остальные — источники, привязываемые к нему.
    """
    groups: list[list[Event]] = []
    for event in events:
        for group in groups:
            if _similarity(group[0], event) >= THRESHOLD:
                group.append(event)
                break
        else:
            groups.append([event])
    return groups