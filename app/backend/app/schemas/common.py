"""Общие схемы: конверт списка и формат ошибки."""
from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Единый конверт всех list-эндпоинтов.

    `hint` заполняется только при `total == 0` — что смягчить, чтобы нашлось (06_MAX_и_UX.md, п. 4).
    """

    items: list[T]
    total: int
    hint: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict | list] = None


class ErrorBody(BaseModel):
    error: ErrorDetail
