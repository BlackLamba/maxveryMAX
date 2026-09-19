"""health, cities, categories + общий формат ошибок."""
import pytest


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["service"] == "maxveryMAX-backend"


async def test_cities(client):
    r = await client.get("/api/cities")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    slugs = {c["slug"] for c in body["items"]}
    assert {"moscow", "st_petersburg", "kazan", "sochi"} == slugs
    assert body["hint"] is None


async def test_categories(client):
    r = await client.get("/api/categories")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 8
    by_slug = {c["slug"]: c["name"] for c in body["items"]}
    assert by_slug["concert"] == "Концерт"
    # порядок — по sort_order
    assert body["items"][0]["slug"] == "concert"


async def test_unknown_route_error_format(client):
    r = await client.get("/api/definitely-not-here")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]


async def test_validation_error_format(client):
    r = await client.get("/api/events", params={"limit": 0})
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list) and body["error"]["details"]


async def test_time_window_requires_single_day(client):
    r = await client.get(
        "/api/events",
        params={"time_from": "18:00", "date_from": "2026-09-19"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "validation_error"
