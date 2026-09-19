"""Таблицы каталога: events, event_sources, event_tags."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import PGJSON


class EventORM(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_city_start", "city_id", "starts_at"),
        Index("ix_events_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    #: slug провайдера, который записал событие (mock/timepad/kudago/culture)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    venue_name: Mapped[Optional[str]] = mapped_column(String(300))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    price_min: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    price_max: Mapped[Optional[int]] = mapped_column(Integer)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    age_limit: Mapped[Optional[str]] = mapped_column(String(8))
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    data_origin: Mapped[str] = mapped_column(String(16), default="mock")  # mock|live
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|sold_out|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["CategoryORM"] = relationship("CategoryORM", lazy="joined")  # noqa: F821
    city: Mapped["CityORM"] = relationship("CityORM", lazy="joined")  # noqa: F821
    sources: Mapped[list["EventSourceORM"]] = relationship(
        "EventSourceORM", back_populates="event", cascade="all, delete-orphan"
    )


class EventSourceORM(Base):
    __tablename__ = "event_sources"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_event_sources_source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(32))  # slug провайдера
    source_id: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    raw: Mapped[Optional[dict]] = mapped_column(PGJSON)

    event: Mapped["EventORM"] = relationship("EventORM", back_populates="sources")


class EventTagORM(Base):
    __tablename__ = "event_tags"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
