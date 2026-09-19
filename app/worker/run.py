"""Точка входа контейнера worker. Всегда периодический цикл."""
from __future__ import annotations

import asyncio
import logging

from .config import LOG_LEVEL
from .scheduler import run_loop

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    asyncio.run(run_loop())


if __name__ == "__main__":
    main()