"""Ранжирование: баллы, порядок, reason."""


async def test_relevance_order_and_reason(client, today):
    d = today.isoformat()
    r = await client.get(
        "/api/events",
        params={
            "city_id": 1,
            "date_from": d,
            "date_to": d,
            "time_from": "18:00",
            "time_to": "21:00",
            "price_max": 1500,
            "lat": 55.7522,
            "lon": 37.6156,
            "radius_km": 10,
        },
    )
    body = r.json()
    items = body["items"]
    # Прошли фильтры: джаз (500, в окне, рядом), выставка (500, в окне),
    # лекция (0, в окне), мастер-класс (0, в окне)
    assert body["total"] == 4
    scores = [i["score"] for i in items]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)

    # Каждому — осмысленный reason
    for i in items:
        assert i["reason"]
        assert i["reason"] != ""

    # Джаз: в окне + бюджет + рядом — все три фрагмента
    jazz = next(i for i in items if i["title"].startswith("Джазовый"))
    assert "в ваше время" in jazz["reason"]
    assert "бюджет" in jazz["reason"]
    assert "рядом" in jazz["reason"]

    # Лекция — бесплатно
    lecture = next(i for i in items if i["title"].startswith("Лекция"))
    assert "бесплатно" in lecture["reason"].lower()


async def test_score_transparency_and_neutral_reason(client):
    r = await client.get("/api/events/1")
    body = r.json()
    assert body["score"] is not None
    assert body["reason"]  # без фильтров — фолбэк
    assert "по вашим фильтрам" in body["reason"]


async def test_preferences_bonus(client, today):
    # Сохраняем предпочтение «concert» для пользователя
    r = await client.post(
        "/api/preferences",
        json={"user_id": "pref-user", "categories": ["concert"]},
    )
    assert r.status_code == 201

    d = today.isoformat()
    base_resp = await client.get(
        "/api/events",
        params={"city_id": 1, "date_from": d, "date_to": d, "category": "concert"},
    )
    base = base_resp.json()
    with_pref_resp = await client.get(
        "/api/events",
        params={
            "city_id": 1,
            "date_from": d,
            "date_to": d,
            "category": "concert",
            "user_id": "pref-user",
        },
    )
    with_pref = with_pref_resp.json()

    same_ids = [i["title"] for i in base["items"]] == [i["title"] for i in with_pref["items"]]
    # Балл с предпочтением выше
    for b, p in zip(base["items"], with_pref["items"]):
        if b["id"] == p["id"]:
            assert p["score"] >= b["score"]
            if p["category"] in ("concert",):
                assert p["score"] == b["score"] + 5
    assert same_ids
