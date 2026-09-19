"""GET /api/events: жёсткие фильтры, сортировки, конверт, hint."""
from urllib.parse import quote


def _qs(params: dict) -> str:
    from urllib.parse import urlencode

    return urlencode(params, doseq=True)


async def test_envelope_shape(client):
    r = await client.get("/api/events")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"items", "total", "hint"}
    assert body["total"] == len(body["items"])
    item = body["items"][0]
    for key in (
        "id", "title", "category", "category_name", "city_name", "starts_at",
        "price_display", "is_free", "source_url", "data_origin", "reason",
    ):
        assert key in item, f"нет поля {key}"


async def test_category_hard_filter(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "category": "concert"}),
    )
    body = r.json()
    # Москва сегодня: «Джазовый вечер» (19:00) и «Рок-ночь» (20:00); вчерашний — вне даты
    assert body["total"] == 2
    assert all(i["category"] == "concert" for i in body["items"])


async def test_price_max_filter(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "category": "concert", "price_max": 1000}),
    )
    body = r.json()
    assert body["total"] == 1  # джаз за 500; рок за 2500 отсеклён
    assert body["items"][0]["title"].startswith("Джазовый")


async def test_is_free_filter(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "is_free": "true"}),
    )
    body = r.json()
    assert body["total"] == 2  # лекция и мастер-класс
    assert all(i["is_free"] and i["price_display"] == "Бесплатно" for i in body["items"])


async def test_time_window(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "time_from": "18:00", "time_to": "19:30"}),
    )
    body = r.json()
    titles = {i["title"] for i in body["items"]}
    # старты в окне: лекция 18:00, выставка 18:30, джаз 19:00
    assert body["total"] == 3
    assert "Лекция «Как планировать личный бюджет»" in titles
    assert "Рок-ночь «Напряжение»" not in titles


async def test_radius_filter(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({
            "city_id": 1, "date_from": d, "date_to": d,
            "lat": 55.7522, "lon": 37.6156, "radius_km": 3,
        }),
    )
    body = r.json()
    # в радиусе 3 км: джаз, выставка, лекция, мастер-класс (рок ~13 км — нет)
    assert body["total"] == 4
    for i in body["items"]:
        assert i["distance_km"] is not None and i["distance_km"] <= 3.0
    assert "Рок-ночь «Напряжение»" not in {i["title"] for i in body["items"]}


async def test_sort_price_asc(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "sort": "price_asc"}),
    )
    items = r.json()["items"]
    assert items[0]["price_display"] == "Бесплатно"


async def test_sort_distance_requires_coords(client):
    r = await client.get("/api/events", params={"sort": "distance"})
    assert r.status_code == 400


async def test_sort_distance(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({
            "city_id": 1, "date_from": d, "date_to": d,
            "lat": 55.7522, "lon": 37.6156, "sort": "distance",
        }),
    )
    items = r.json()["items"]
    dists = [i["distance_km"] for i in items]
    assert dists == sorted(dists)
    assert dists[0] <= 1.5  # ближайший — около центра


async def test_empty_result_with_hint(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params=_qs({"city_id": 1, "date_from": d, "date_to": d, "category": "theater"}),
    )
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["hint"]
    assert "По этим условиям ничего не нашлось" in body["hint"]


async def test_detail_event(client):
    r = await client.get("/api/events/1")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["city_name"] == "Москва"
    assert body["reason"]
    assert body["provider"] == "Демо-набор"
    assert body["data_origin"] == "mock"


async def test_detail_event_404(client):
    r = await client.get("/api/events/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_detail_reason_with_filters(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events/1",
        params=_qs({"date_from": d, "date_to": d, "time_from": "18:00", "time_to": "21:00", "price_max": 1500}),
    )
    body = r.json()
    assert "19:00" in body["reason"] or "в ваше время" in body["reason"]
    assert "бюджет" in body["reason"]


async def test_price_display_variants(client):
    r = await client.get("/api/events", params={"limit": 50})
    displays = {i["title"]: i["price_display"] for i in r.json()["items"]}
    assert displays["Джазовый вечер «Синяя луна»"] == "500–1200 ₽"
    assert displays["Выставка «Свет XX века»"] == "500 ₽"
    assert displays["Лекция «Как планировать личный бюджет»"] == "Бесплатно"
