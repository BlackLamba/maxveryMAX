"""Единый формат ошибок API и exception handlers.

Формат: {"error": {"code": "...", "message": "...", "details": ...}}
Коды: validation_error (400), not_found (404), http_error, server_error (500).
"""
from __future__ import annotations

import logging

import pydantic
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("maxveryMAX.backend.errors")


class ApiValidation(Exception):
    """Ошибка валидации бизнес-правил (→ 400 validation_error)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ApiNotFound(Exception):
    """Сущность не найдена (→ 404 not_found)."""

    def __init__(self, message: str = "не найдено") -> None:
        super().__init__(message)
        self.message = message


def _body(code: str, message: str, details: dict | list | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiValidation)
    async def _api_validation(_: Request, exc: ApiValidation) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_body("validation_error", exc.message, exc.details),
        )

    @app.exception_handler(ApiNotFound)
    async def _api_not_found(_: Request, exc: ApiNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_body("not_found", exc.message),
        )

    @app.exception_handler(HTTPException)
    async def _http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        # неизвестные маршруты и прочий «vanilla»-404 FastAPI — в общий формат
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content=_body("not_found", "не найдено"))
        message = exc.detail if isinstance(exc.detail, str) else "ошибка запроса"
        return JSONResponse(
            status_code=exc.status_code,
            content=_body("http_error", message),
        )

    @app.exception_handler(RequestValidationError)
    async def _pydantic_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "loc": [str(part) for part in err.get("loc", [])],
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_body("validation_error", "некорректные параметры запроса", details),
        )

    @app.exception_handler(pydantic.ValidationError)
    async def _raw_pydantic_validation(_: Request, exc: pydantic.ValidationError) -> JSONResponse:
        # Модель-зависимость (Annotated[EventFilters, Depends()]) валидируется
        # при вызове зависимости — FastAPI её НЕ оборачивает в RequestValidationError,
        # поэтому ловим «сырой» ValidationError и отдаём тот же формат 400.
        details = [
            {
                "loc": [str(part) for part in err.get("loc", [])],
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_body("validation_error", "некорректные параметры запроса", details),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Не глотаем молча: логируем с traceback и отдаём понятный ответ (app/README.md, п. 9).
        logger.exception("unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_body("server_error", "внутренняя ошибка сервера"),
        )
