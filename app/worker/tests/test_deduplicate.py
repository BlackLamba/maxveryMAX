from datetime import datetime, timezone

from shared.models import Event

from worker.pipeline.deduplicate import deduplicate


def _ev(title: str, starts_at: datetime, venue: str = "A") -> Event:
    return Event(
        title=title,
        category="concert",
        city_slug="moscow",
        venue_name=venue,
        starts_at=starts_at,
        source_id=title,
    )


def test_duplicates_are_grouped():
    t = datetime(2026, 9, 20, 20, 0, tzinfo=timezone.utc)
    events = [
        _ev("Ночной джаз в подвале", t),
        _ev("Ночной джаз в подвале!", t),
        _ev("Совсем другое событие", t),
    ]
    groups = deduplicate(events)
    assert len(groups) == 2
    assert len(groups[0]) == 2