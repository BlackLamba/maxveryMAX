"""Конфигурация backend: все переменные окружения читаются здесь.

Конвенция (app/README.md, раздел 9): os.environ по коду не трогаем —
только через Settings. Образец переменных — app/.env.example.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- общие ---
    app_env: str = "dev"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    # --- база данных ---
    # Продакшн/докер: PostgreSQL (asyncpg). Для локальных экспериментов допустим SQLite:
    #   sqlite+aiosqlite:///./dev.db
    database_url: str = "postgresql+asyncpg://maxuser:maxpass@postgres:5432/maxevents"

    # --- API ---
    #: Запятый список допустимых origin; "*" — все (демо-режим хакатона).
    cors_origins: str = "*"

    # --- домен ---
    #: Смещение от UTC для городов, если город не задан (MVP: все демо-города UTC+3).
    default_tz_offset_hours: int = 3
    #: Максимум кандидатов, по которым считаются баллы ранжирования за один запрос.
    max_candidates: int = 500

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
