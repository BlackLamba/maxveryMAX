"""Точка входа backend: FastAPI, CORS, обработчики ошибок, роутеры."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .api import analytics, categories, cities, events, favorites, health, preferences, search
from .config import get_settings
from .errors import register_exception_handlers

logger = logging.getLogger("maxveryMAX.backend")


def create_app() -> FastAPI:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = FastAPI(
        title="maxveryMAX backend",
        version=__version__,
        description=(
            "API афиши: поиск с фильтрами, ранжирование с объяснением «почему подходит», "
            "карточка события, избранное, предпочтения и аналитика кликов. "
            "Данные читает только из PostgreSQL (наполняет worker/)."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,  # для демо: miniapp ходит через nginx-прокси /api
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.middleware("http")
    async def _unified_404(request: Request, call_next):
        # Starlette отвечает «сырым» PlainText 404 на неизвестные маршруты (до
        # exception handler'ов) — перекрашиваем в единый JSON-формат.
        response = await call_next(request)
        if response.status_code == 404 and request.url.path.startswith(
            settings.api_prefix + "/"
        ):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {"code": "not_found", "message": "не найдено", "details": None}
                },
            )
        return response

    prefix = settings.api_prefix
    for module in (health, cities, categories, events, search, favorites, preferences, analytics):
        app.include_router(module.router, prefix=prefix)

    return app


app = create_app()
