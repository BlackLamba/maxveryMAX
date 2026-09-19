from __future__ import annotations

import asyncio
import logging

from .config import ENABLED_PROVIDERS, SYNC_INTERVAL_MINUTES
from .db import SessionLocal
from .providers import MockProvider
from .repository import upsert_many

log = logging.getLogger(__name__)


def _build_providers() -> list:
    providers = []
    for name in ENABLED_PROVIDERS:
        if name == "mock":
            providers.append(MockProvider())
        # kudago/timepad — когда появятся реализации
    return providers


async def run_once() -> int:
    providers = _build_providers()
    total = 0
    async with SessionLocal() as session:
        for provider in providers:
            events = await provider.fetch_events()
            n = await upsert_many(session, events)
            log.info("Provider %s: upserted %d events", provider.name, n)
            total += n
    return total


async def run_loop() -> None:
    interval = SYNC_INTERVAL_MINUTES * 60
    while True:
        try:
            n = await run_once()
            log.info("Sync cycle done, %d events", n)
        except Exception:
            log.exception("Sync cycle failed")
        await asyncio.sleep(interval)