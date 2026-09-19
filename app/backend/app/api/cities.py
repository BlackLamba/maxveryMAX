"""GET /api/cities — справочник городов."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..repositories import references_repo
from ..schemas.common import Envelope
from ..schemas.events import CityOut

router = APIRouter(tags=["references"])


@router.get("/cities", response_model=Envelope[CityOut])
async def list_cities(db: AsyncSession = Depends(get_db)) -> Envelope[CityOut]:
    rows = await references_repo.list_cities(db)
    return Envelope(items=[CityOut.model_validate(r) for r in rows], total=len(rows))
