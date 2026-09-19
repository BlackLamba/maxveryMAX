from __future__ import annotations

import os
from pathlib import Path

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://maxuser:maxpass@localhost:5432/maxevents",
)

SYNC_INTERVAL_MINUTES: int = int(os.environ.get("SYNC_INTERVAL_MINUTES", "60"))

TIMEPAD_API_TOKEN: str = os.environ.get("TIMEPAD_API_TOKEN", "")
KUDAGO_API_TOKEN: str = os.environ.get("KUDAGO_API_TOKEN", "")

#: Провайдеры, включаемые в периодический цикл `run`.
ENABLED_PROVIDERS: tuple[str, ...] = tuple(
    p.strip() for p in os.environ.get("ENABLED_PROVIDERS", "mock").split(",") if p.strip()
)

DATA_DIR: Path = Path(__file__).parent / "data"
MOCK_EVENTS_PATH: Path = DATA_DIR / "mock_events.json"

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")