"""Ожидание готовности БД (entrypoint backend; работает и для SQLite)."""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("wait_for_db: DATABASE_URL не задан, пропускаю ожидание", file=sys.stderr)
        return
    if url.startswith("sqlite"):
        return  # локальный файл не нужно ждать
    engine = create_async_engine(url, pool_pre_ping=True)
    for attempt in range(60):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"wait_for_db: БД готова (попытка {attempt + 1})")
            break
        except Exception as exc:  # noqa: BLE001
            print(f"wait_for_db: БД не готова ({exc.__class__.__name__}), жду…")
            await asyncio.sleep(1)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
