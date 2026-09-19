"""ORM-модели backend. Импортируем всё, чтобы Base.metadata видела все таблицы."""
from ..db import Base
from .base import PGJSON
from .event import EventORM, EventSourceORM, EventTagORM
from .reference import CategoryORM, CityORM, ProviderORM, TagORM
from .user import (
    ACTION_CLICK_SOURCE,
    ACTION_FAV_ADD,
    ACTION_FAV_REMOVE,
    ACTION_VIEW,
    EventInteractionORM,
    FavoriteORM,
    UserORM,
    UserPreferencesORM,
)

__all__ = [
    "ACTION_CLICK_SOURCE",
    "Base",
    "ACTION_FAV_ADD",
    "ACTION_FAV_REMOVE",
    "ACTION_VIEW",
    "CategoryORM",
    "CityORM",
    "EventInteractionORM",
    "EventORM",
    "EventSourceORM",
    "EventTagORM",
    "FavoriteORM",
    "PGJSON",
    "ProviderORM",
    "TagORM",
    "UserORM",
    "UserPreferencesORM",
]
