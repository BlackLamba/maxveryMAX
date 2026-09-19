"""Справочники: города, категории."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CategoryORM, CityORM


async def list_cities(db: AsyncSession) -> list[CityORM]:
    result = await db.execute(select(CityORM).order_by(CityORM.name))
    return list(result.scalars().all())


async def list_categories(db: AsyncSession) -> list[CategoryORM]:
    result = await db.execute(
        select(CategoryORM).order_by(CategoryORM.sort_order, CategoryORM.name)
    )
    return list(result.scalars().all())


async def city_tz_offset(db: AsyncSession, city_id: Optional[int]) -> Optional[int]:
    if city_id is None:
        return None
    result = await db.execute(select(CityORM.tz_offset_hours).where(CityORM.id == city_id))
    return result.scalar_one_or_none()


async def city_id_by_slug(db: AsyncSession, slug: str) -> Optional[int]:
    result = await db.execute(select(CityORM.id).where(CityORM.slug == slug))
    return result.scalar_one_or_none()


async def city_by_id(db: AsyncSession, city_id: int) -> Optional[CityORM]:
    result = await db.execute(select(CityORM).where(CityORM.id == city_id))
    return result.scalar_one_or_none()
