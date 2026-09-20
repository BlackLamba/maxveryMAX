"""
Обработчики команд бота.

Бот у нас тонкий: только /start (приветствие + кнопка открытия мини-аппа),
/help и фоллбэк на любые другие сообщения. Весь сбор параметров — в miniapp,
здесь state machine не нужна (см. docs/02_user_journey.md и Аналитик/06_MAX_и_UX.md).
"""

from __future__ import annotations

import logging

from maxapi import Bot, Dispatcher, F
from maxapi.filters.command import Command, CommandStart
from maxapi.types import BotStarted, MessageCreated
from maxapi.types import OpenAppButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from . import texts

logger = logging.getLogger(__name__)

dp = Dispatcher()


def _build_open_app_keyboard(bot_username: str, bot_user_id: int) -> object:
    """Собирает inline-клавиатуру с одной кнопкой открытия мини-приложения."""
    builder = InlineKeyboardBuilder()
    # web_app=ник_бота, contact_id=id_бота — так MAX понимает, какое именно
    # мини-приложение открыть (оно привязано к боту в настройках партнёрской
    # платформы, URL прописывается там же, см. dev.max.ru/docs/webapps).
    builder.row(
        OpenAppButton(
            text=texts.OPEN_APP_BUTTON_TEXT,
            web_app=bot_username,
            contact_id=bot_user_id,
        )
    )
    return builder.as_markup()


# --- Событие BotStarted (пользователь нажал «Начать» в профиле бота) -------

@dp.bot_started()
async def on_bot_started(event: BotStarted) -> None:
    kb = _build_open_app_keyboard(
        bot_username=event.bot.me.username,
        bot_user_id=event.bot.me.user_id,
    )
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=texts.START_MESSAGE,
        attachments=[kb],
    )


# --- Команда /start --------------------------------------------------------

@dp.message_created(CommandStart())
async def on_start(event: MessageCreated) -> None:
    kb = _build_open_app_keyboard(
        bot_username=event.bot.me.username,
        bot_user_id=event.bot.me.user_id,
    )
    await event.message.answer(text=texts.START_MESSAGE, attachments=[kb])


# --- Команда /help ---------------------------------------------------------

@dp.message_created(Command("help"))
async def on_help(event: MessageCreated) -> None:
    kb = _build_open_app_keyboard(
        bot_username=event.bot.me.username,
        bot_user_id=event.bot.me.user_id,
    )
    await event.message.answer(text=texts.HELP_MESSAGE, attachments=[kb])


# --- Фоллбэк: любые другие текстовые сообщения -----------------------------

@dp.message_created(F.message.body.text)
async def on_any_text(event: MessageCreated) -> None:
    # Игнорируем пустые и системные, просто подсказываем /help
    kb = _build_open_app_keyboard(
        bot_username=event.bot.me.username,
        bot_user_id=event.bot.me.user_id,
    )
    await event.message.answer(text=texts.FALLBACK_MESSAGE, attachments=[kb])
