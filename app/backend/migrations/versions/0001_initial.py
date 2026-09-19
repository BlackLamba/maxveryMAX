"""0001 — начальная схема (cities, categories, providers, tags, events,
event_sources, event_tags, users, favorites, user_preferences, event_interactions).

Схема создаётся из Base.metadata ORM-моделей — единый источник истины
(избегаем рассинхрона «миграция vs модели»). Для MVP этого достаточно;
дальнейшие изменения схемы — обычными autogenerate-ревайзами поверх 0001.
"""
from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    from app.models import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind)
