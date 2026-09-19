"""Совместимый JSON-тип: JSONB на PostgreSQL, JSON на SQLite (тесты/dev)."""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

PGJSON = JSON().with_variant(JSONB, "postgresql")
