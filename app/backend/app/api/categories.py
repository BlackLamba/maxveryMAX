"""GET /api/categories — справочник категорий (источник — shared/categories)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..repositories import references_repo
from ..schemas.common import Envelope
from ..schemas.events import CategoryOut

router = APIRouter(tags=["references"])


@router.get("/categories", response_model=Envelope[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> Envelope[CategoryOut]:
    rows = await references_repo.list_categories(db)
    return Envelope(items=[CategoryOut.model_validate(r) for r in rows], total=len(rows))
