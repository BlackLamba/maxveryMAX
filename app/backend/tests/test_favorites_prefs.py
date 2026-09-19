"""Избранное и предпочтения."""


async def test_favorites_lifecycle(client):
    # add
    r = await client.post("/api/favorites", json={"user_id": "u-fav", "event_id": 2})
    assert r.status_code == 201
    assert r.json() == {"ok": True}

    # дубль идемпотентен
    r = await client.post("/api/favorites", json={"user_id": "u-fav", "event_id": 2})
    assert r.status_code == 201

    # list
    r = await client.get("/api/favorites", params={"user_id": "u-fav"})
    body = r.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["id"] == 2
    assert item["added_at"]
    assert item["title"].startswith("Выставка")

    # remove
    r = await client.delete("/api/favorites/2", params={"user_id": "u-fav"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # после удаления — пусто
    r = await client.get("/api/favorites", params={"user_id": "u-fav"})
    assert r.json()["total"] == 0

    # повторное удаление — 404
    r = await client.delete("/api/favorites/2", params={"user_id": "u-fav"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"

    # несуществующее событие — 404
    r = await client.post("/api/favorites", json={"user_id": "u-fav", "event_id": 99999})
    assert r.status_code == 404


async def test_preferences_save_and_read(client):
    r = await client.post(
        "/api/preferences",
        json={"user_id": "u-pref", "categories": ["concert", "theater"], "price_max": 1000},
    )
    assert r.status_code == 201
    assert r.json()["saved"] is True
    assert r.json()["categories"] == ["concert", "theater"]
    assert r.json()["price_max"] == 1000

    r = await client.get("/api/preferences", params={"user_id": "u-pref"})
    body = r.json()
    assert body["saved"] is True
    assert body["categories"] == ["concert", "theater"]
    assert body["price_max"] == 1000

    # нового пользователя нет → saved=false, дефолты
    r = await client.get("/api/preferences", params={"user_id": "nobody-here"})
    body = r.json()
    assert body["saved"] is False
    assert body["categories"] == []
    assert body["price_max"] is None


async def test_preferences_update(client):
    await client.post("/api/preferences", json={"user_id": "u-upd", "price_max": 500})
    r = await client.post(
        "/api/preferences",
        json={"user_id": "u-upd", "categories": ["exhibition"], "radius_km": 8},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["categories"] == ["exhibition"]
    assert body["price_max"] is None  # не передано — сбросили
    assert body["radius_km"] == 8
