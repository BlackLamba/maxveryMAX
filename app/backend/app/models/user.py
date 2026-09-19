"""Пользовательские таблицы: users, favorites, user_preferences, event_interactions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base
from .base import PGJSON

# Действия в event_interactions:
ACTION_VIEW = "view"
ACTION_CLICK_SOURCE = "click_source"
ACTION_FAV_ADD = "favorite_add"
ACTION_FAV_REMOVE = "favorite_remove"


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: uid из MAX initData (бот/мини-апп передают как user_id)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FavoriteORM(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_favorites_user_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserPreferencesORM(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    #: список slug категорий
    categories: Mapped[list] = mapped_column(PGJSON, default=list)
    price_max: Mapped[Optional[int]] = mapped_column(Integer)
    radius_km: Mapped[Optional[float]] = mapped_column(Float)
    # onupdate=func.now() намеренно НЕ ставим: server-side обновление гонит
    # attribute-expiry, а ленивая подгрузка в async-сессии запрещена.
    # updated_at при обновлении выставляет user_repo.upsert_preferences.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EventInteractionORM(Base):
    __tablename__ = "event_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(32), index=True)
    meta: Mapped[Optional[dict]] = mapped_column(PGJSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
