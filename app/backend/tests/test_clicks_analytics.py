"""Клики на источник и аналитика (метрика пилота)."""


async def test_click_logs_transition(client):
    r = await client.post("/api/events/1/click", json={"user_id": "u-click"})
    assert r.status_code == 201
    assert r.json() == {"ok": True}

    # повторный клик тоже логируется
    r = await client.post("/api/events/1/click", json={"user_id": "u-click"})
    assert r.status_code == 201

    r = await client.post("/api/events/3/click", json={"user_id": "u-click", "meta": {"from": "miniapp"}})
    assert r.status_code == 201

    r = await client.get("/api/analytics/summary", params={"user_id": "u-click"})
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "u-click"
    assert body["clicks_to_source"] == 3
    assert body["top_categories"]["concert"] == 2  # джаз + (лекция — lecture)
    assert body["top_categories"]["lecture"] == 1


async def test_click_anonymous(client):
    r = await client.post("/api/events/5/click", json={})
    assert r.status_code == 201


async def test_click_unknown_event_404(client):
    r = await client.post("/api/events/99999/click", json={"user_id": "u-click"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_analytics_new_user_zeroes(client):
    r = await client.get("/api/analytics/summary", params={"user_id": "fresh-user"})
    assert r.status_code == 200
    body = r.json()
    assert body["clicks_to_source"] == 0
    assert body["favorites"] == 0
    assert body["top_categories"] == {}


async def test_favorites_reflected_in_analytics(client):
    await client.post("/api/favorites", json={"user_id": "u-count", "event_id": 4})
    r = await client.get("/api/analytics/summary", params={"user_id": "u-count"})
    assert r.json()["favorites"] == 1
