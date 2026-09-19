"""POST /api/search и /api/search/natural."""
from urllib.parse import urlencode

from app.services.natural import parse_natural
from app.services.timeutils import today_local

TODAY = today_local(3)


async def test_search_endpoint_same_as_get(client, today):
    d = today.isoformat()
    r = await client.post(
        "/api/search",
        json={"city_id": 1, "date_from": d, "date_to": d, "category": ["concert"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert all(i["category"] == "concert" for i in body["items"])


async def test_parse_natural_evening_concert_budget():
    f, understood, city = parse_natural("концерт сегодня вечером до 1500₽", TODAY)
    assert f.category == ["concert"]
    assert f.date_from == f.date_to == TODAY
    assert f.time_from is not None and f.time_to is not None
    assert f.price_max == 1500
    assert "вечер" in " ".join(understood).lower() or any("17:00" in u for u in understood)


async def test_parse_natural_free_lecture():
    f, understood, _ = parse_natural("бесплатная лекция завтра", TODAY)
    assert f.is_free is True
    assert f.category == ["lecture"]
    from datetime import timedelta

    assert f.date_from == TODAY + timedelta(days=1)


async def test_parse_natural_near_and_city():
    f, understood, city = parse_natural("выставка рядом в казань", TODAY)
    assert f.radius_km == 5
    assert city == "kazan"
    assert f.category == ["exhibition"]


async def test_parse_natural_nothing_understood():
    f, understood, city = parse_natural("ксыва ждтлш", TODAY)
    assert understood == []
    assert city is None


async def test_parse_natural_word_boundary_art():
    # «картинг» не должен давать категорию exhibition
    f, understood, _ = parse_natural("картинг для детей", TODAY)
    assert f.category in (None, ["children"])


async def test_natural_endpoint_full(client, today):
    r = await client.post(
        "/api/search/natural",
        json={"query": "концерт сегодня вечером до 1500 рублей"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["understood"]
    assert body["filters"]["price_max"] == 1500
    assert body["filters"]["date_from"] == today.isoformat()
    # джаз (500 ₽, 19:00) должен попасть; рок (2500) — нет
    assert body["total"] >= 1
    assert all(i["price_max"] <= 1500 or i["is_free"] for i in body["items"])


async def test_natural_endpoint_unknown(client):
    r = await client.post("/api/search/natural", json={"query": "яблочный пирог"})
    assert r.status_code == 200
    body = r.json()
    assert body["understood"] == []
    assert body["hint"]


async def test_natural_near_uses_city_center(client):
    r = await client.post(
        "/api/search/natural",
        json={"query": "лекция рядом в москве"},
    )
    body = r.json()
    assert body["filters"]["radius_km"] == 5
    assert body["filters"]["lat"] is not None
    assert any("центр города" in u for u in body["understood"])
    # лекция (55.760, 37.610) в 5 км от центра Москвы (55.7522, 37.6156)
    assert body["total"] >= 1
