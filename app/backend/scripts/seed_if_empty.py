"""Одноразовый seed тестовых данных для Docker-запуска (idempotent).

Ждёт готовности БД, затем:
  - если таблица events пуста  -> наполняет справочники и демо-события
                                 (логика scripts/dev_fill.py, data_origin='mock');
  - если данные уже есть       -> ничего не делает, exit 0 (перезапуск compose безопасен).

Использование:
    DATABASE_URL=... python scripts/seed_if_empty.py
Вызывается сервисом `seed` из docker-compose.yml при первом старте.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = os.path.dirname(BACKEND_DIR)
for _p in (APP_ROOT, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import func, select  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.models import EventORM  # noqa: E402

WAIT_ROUNDS = 30
WAIT_SECONDS = 2


async def _events_count() -> int:
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            return int(await conn.scalar(select(func.count()).select_from(EventORM)) or 0)
    finally:
        await engine.dispose()


#: «таблицы ещё нет» = БД жива, но пуста: не ждём миграции, сеем сразу
_EMPTY_DB_MARKERS = ("no such table", "does not exist", "undefinedtable")


async def main() -> None:
    last_err: Exception | None = None
    count = 0
    for _ in range(WAIT_ROUNDS):
        try:
            count = await _events_count()
            break
        except Exception as err:  # noqa: BLE001 — ждём, пока БД/миграции поднимутся
            if any(m in str(err).lower() for m in _EMPTY_DB_MARKERS):
                count = 0
                break
            last_err = err
            time.sleep(WAIT_SECONDS)
    else:
        raise SystemExit(f"seed_if_empty: БД недоступна после {WAIT_ROUNDS * WAIT_SECONDS} c: {last_err}")

    if count > 0:
        print(f"seed_if_empty: в БД уже {count} событий, seed не требуется")
        return

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dev_fill import main as dev_fill_main  # noqa: E402

    await dev_fill_main()
    print("seed_if_empty: тестовые данные созданы (data_origin='mock')")


if __name__ == "__main__":
    asyncio.run(main())
