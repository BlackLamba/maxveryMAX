from __future__ import annotations

from shared.models import Event  # type: ignore[import-not-found]


def quality_score(event: Event) -> int:
    """Простая эвристика: 0..100. Воркер пересчитывает при upsert."""
    score = 0
    if event.description and len(event.description) > 80:
        score += 30
    if event.image_url:
        score += 20
    if event.price_min is not None:
        score += 15
    if event.lat is not None and event.lon is not None:
        score += 15
    if event.venue_name:
        score += 10
    if event.source_url:
        score += 10
    return min(score, 100)