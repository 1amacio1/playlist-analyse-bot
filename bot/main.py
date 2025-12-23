import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from bot.handlers.playlist_handler import handle_playlist_url
from bot.handlers.callback_handler import (
    handle_city_selection,
    handle_sort,
    handle_pagination,
    handle_recommendations
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class PlaylistStates(StatesGroup):
    waiting_for_url = State()
    processing = State()


user_results = {}


@dp.message(Command(commands="start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет! Я бот для поиска концертов по вашему плейлисту Яндекс Музыки.\n\n"
        "Отправьте мне ссылку на публичный плейлист (можно в формате HTML-кода с iframe), "
        "и я найду концерты ваших любимых артистов!"
    )


@dp.message(Command(commands="help"))
async def help_command(message: Message):
    await message.answer(
        "📖 Как использовать бота:\n\n"
        "1. Скопируйте ссылку на ваш публичный плейлист Яндекс Музыки\n"
        "   Или отправьте HTML-код с iframe плейлиста\n"
        "2. Отправьте ссылку боту\n"
        "3. Дождитесь обработки (это займет 2-3 минуты)\n"
        "4. Получите список концертов с фильтрами и сортировкой\n\n"
        "Примеры:\n"
        "• https://music.yandex.ru/users/USERNAME/playlists/12345\n"
        "• <iframe src='https://music.yandex.ru/iframe/#playlist/USERNAME/12345'>...</iframe>"
    )


@dp.message(F.text | F.html)
async def handle_playlist_message(message: Message, state: FSMContext):
    await handle_playlist_url(message, state, user_results)


@dp.callback_query(F.data.startswith("city_"))
async def handle_city_callback(callback):
    await handle_city_selection(callback, user_results)


@dp.callback_query(F.data.startswith("sort_"))
async def handle_sort_callback(callback):
    await handle_sort(callback, user_results)


@dp.callback_query(F.data.startswith("page_"))
async def handle_page_callback(callback):
    await handle_pagination(callback, user_results)


@dp.callback_query(F.data == "recommendations")
async def handle_recommendations_callback(callback):
    await handle_recommendations(callback, user_results)


@dp.message()
async def handle_other_messages(message: Message):
    await message.answer(
        "Отправьте мне ссылку на публичный плейлист Яндекс Музыки или HTML-код с iframe.\n"
        "Используйте /help для получения инструкций."
    )


async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

