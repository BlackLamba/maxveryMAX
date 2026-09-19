from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import DATABASE_URL

#: Тот же Base, что у backend. Worker использует те же ORM-модели.
from app.models import Base  # noqa: E402  # type: ignore[import-not-found]

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    return SessionLocal()


__all__ = ["Base", "engine", "SessionLocal", "get_session"]