"""Тесты для основного модуля бота"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import User, Message, Chat
from aiogram.fsm.context import FSMContext

from src.bot.main import (
    start_command,
    help_command,
    handle_other_messages,
    bot,
    dp
)


@pytest.mark.asyncio
async def test_start_command():
    """Тест команды /start"""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    
    await start_command(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "Привет" in call_args or "бот" in call_args.lower()


@pytest.mark.asyncio
async def test_help_command():
    """Тест команды /help"""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    
    await help_command(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "плейлист" in call_args.lower() or "инструкции" in call_args.lower()


@pytest.mark.asyncio
async def test_handle_other_messages():
    """Тест обработки других сообщений"""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    
    await handle_other_messages(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "плейлист" in call_args.lower() or "help" in call_args.lower()


@pytest.mark.asyncio
async def test_bot_initialization():
    """Тест инициализации бота"""
    assert bot is not None
    assert dp is not None


def test_dispatcher_handlers():
    """Тест регистрации обработчиков"""
    # Проверяем, что обработчики зарегистрированы
    assert len(dp.message.handlers) > 0
    assert len(dp.callback_query.handlers) > 0

