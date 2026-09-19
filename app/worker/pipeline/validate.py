from __future__ import annotations

from shared.models import Event  # type: ignore[import-not-found]

REQUIRED_FIELDS = ("title", "category", "city_slug", "starts_at", "source_id")


def validate_event(event: Event) -> None:
    """Бросает ValueError, если событие неполное.

    Дублирует Pydantic — чтобы пайплайн был отказоустойчив
    к внешним источникам, где поля могут быть пустыми строками.
    """
    missing = [f for f in REQUIRED_FIELDS if not getattr(event, f, None)]
    if missing:
        raise ValueError(
            f"Event missing required fields: {missing} (source_id={event.source_id!r})"
        )