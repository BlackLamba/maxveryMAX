from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from .config import LOG_LEVEL, MOCK_EVENTS_PATH
from .db import SessionLocal
from .providers import MockProvider
from .repository import upsert_many
from .scheduler import run_loop, run_once

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("worker")


async def _cmd_import(path: str) -> None:
    provider = MockProvider(path=Path(path))
    events = await provider.fetch_events()
    async with SessionLocal() as session:
        n = await upsert_many(session, events)
    log.info("Imported %d events from %s", n, path)


async def _cmd_run() -> None:
    await run_loop()


async def _cmd_once() -> None:
    n = await run_once()
    log.info("One-shot sync: %d events", n)


def main() -> None:
    parser = argparse.ArgumentParser(prog="worker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_import = sub.add_parser("import", help="Разовый импорт JSON")
    p_import.add_argument("--file", default=str(MOCK_EVENTS_PATH))

    sub.add_parser("run", help="Периодический цикл")
    sub.add_parser("once", help="Один цикл")

    args = parser.parse_args()
    if args.cmd == "import":
        asyncio.run(_cmd_import(args.file))
    elif args.cmd == "run":
        asyncio.run(_cmd_run())
    elif args.cmd == "once":
        asyncio.run(_cmd_once())


if __name__ == "__main__":
    main()