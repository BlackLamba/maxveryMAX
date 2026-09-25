from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from shared.models import Event  # type: ignore[import-not-found]

from ..pipeline.kudago_mapping import map_category, map_city

log = logging.getLogger(__name__)

BASE_URL = "https://kudago.com/public-api/v1.4/events/"
PAGE_SIZE = 100
MAX_PAGES = 5  # MVP: не более 500 событий за один прогон
TIMEOUT = 15.0

#: Поля, которые запрашиваем — держим ответ компактным.
FIELDS = ",".join([
    "id", "title", "description", "dates", "place", "location",
    "categories", "tags", "price", "is_free", "age_restriction",
    "images", "site_url", "favorites_count",
])


class KudaGoProvider:
    """KudaGo Public API. Токен не нужен, есть rate-limit."""

    name = "kudago"

    def __init__(self, locations: list[str] | None = None) -> None:
        #: Ограничение по городам. None → все доступные.
        self.locations = locations or ["msk", "spb", "kzn"]

    async def fetch_events(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Event]:
        since_ts = int((since or datetime.now(timezone.utc)).timestamp())
        params_base: dict[str, str | int] = {
            "fields": FIELDS,
            "expand": "place,dates",
            "text_format": "plain",
            "page_size": PAGE_SIZE,
            "actual_since": since_ts,
            "order_by": "publication_date",
        }
        if until:
            params_base["actual_until"] = int(until.timestamp())

        events: list[Event] = []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for location in self.locations:
                page = 1
                while page <= MAX_PAGES:
                    params = dict(params_base, location=location, page=page)
                    try:
                        resp = await client.get(BASE_URL, params=params)
                        resp.raise_for_status()
                    except httpx.HTTPError as e:
                        log.warning("KudaGo %s page=%s failed: %s", location, page, e)
                        break

                    data = resp.json()
                    results = data.get("results") or []
                    if not results:
                        break

                    for raw in results:
                        event = self._to_event(raw)
                        if event is not None:
                            events.append(event)

                    if not data.get("next"):
                        break
                    page += 1

        log.info("KudaGo: fetched %d events", len(events))
        return events

    def _to_event(self, raw: dict) -> Event | None:
        location_slug = (raw.get("location") or {}).get("slug")
        city_slug = map_city(location_slug) if location_slug else None
        if city_slug is None:
            return None

        categories = [c.get("slug") for c in (raw.get("categories") or []) if c.get("slug")]
        category = map_category(categories)
        if category is None:
            return None

        dates = raw.get("dates") or []
        start_ts = next((d.get("start") for d in dates if d.get("start")), None)
        end_ts = next((d.get("end") for d in dates if d.get("end")), None)
        if start_ts is None:
            return None

        place = raw.get("place") or {}
        coords = place.get("coords") or {}
        images = raw.get("images") or []
        image_url = next((img.get("image") for img in images if img.get("image")), None)

        price_min, price_max, is_free = self._parse_price(raw)

        return Event(
            title=raw.get("title") or "Без названия",
            description=raw.get("description") or "",
            category=category,
            city_slug=city_slug,
            provider=self.name,
            venue_name=place.get("title"),
            address=place.get("address"),
            lat=coords.get("lat"),
            lon=coords.get("lon"),
            starts_at=datetime.fromtimestamp(start_ts, tz=timezone.utc),
            ends_at=datetime.fromtimestamp(end_ts, tz=timezone.utc) if end_ts else None,
            price_min=price_min,
            price_max=price_max,
            is_free=is_free,
            age_limit=raw.get("age_restriction"),
            image_url=image_url,
            source=self.name,
            source_id=str(raw["id"]),
            source_url=raw.get("site_url"),
            data_origin="live",
            tags=[t.get("slug") for t in (raw.get("tags") or []) if t.get("slug")],
            status="active",
        )

    @staticmethod
    def _parse_price(raw: dict) -> tuple[int | None, int | None, bool]:
        if raw.get("is_free"):
            return 0, 0, True
        price = raw.get("price")
        if not price or not isinstance(price, str):
            return None, None, False
        # KudaGo отдаёт либо "1000", либо "1000-2000", либо "бесплатно"
        if "бесплат" in price.lower():
            return 0, 0, True
        parts = [p.strip() for p in price.replace("—", "-").split("-")]
        try:
            nums = [int(p) for p in parts if p.isdigit()]
        except ValueError:
            return None, None, False
        if not nums:
            return None, None, False
        return min(nums), max(nums), False