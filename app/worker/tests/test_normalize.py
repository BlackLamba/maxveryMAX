from datetime import datetime, timezone

from shared.models import Event

from worker.pipeline.normalize import normalize
from worker.pipeline.validate import validate_event


def test_normalize_sets_provider_and_origin():
    raw = {
        "title": "Джаз",
        "category": "concert",
        "city_slug": "moscow",
        "starts_at": "2026-09-20T20:00:00+03:00",
        "source_id": "abc-1",
    }
    event = normalize(raw, provider="mock")
    assert isinstance(event, Event)
    assert event.source == "mock"
    assert event.provider == "mock"
    assert event.data_origin == "mock"


def test_validate_catches_missing_source_id():
    event = Event(
        title="X",
        category="concert",
        city_slug="moscow",
        starts_at=datetime(2026, 9, 20, 20, 0, tzinfo=timezone.utc),
        source_id="",
    )
    try:
        validate_event(event)
    except ValueError:
        return
    raise AssertionError("validate_event should raise on empty source_id")