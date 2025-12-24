import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import User, Message, Chat, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.handlers.playlist_handler import handle_playlist_url, ConcertService
from src.bot.handlers.callback_handler import (
    handle_city_selection,
    handle_sort,
    handle_pagination,
    handle_recommendations
)

@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.text = "https://music.yandex.ru/users/test/playlists/123"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message

@pytest.fixture
def mock_callback():
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.data = "city_moscow"
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback

@pytest.fixture
def mock_state():
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    return state

@pytest.fixture
def user_results():
    return {}

@pytest.mark.asyncio
async def test_handle_city_selection(mock_callback, user_results):

    user_results[12345] = {
        'concerts': [],
        'original_concerts': [],
        'available_cities': ['Москва', 'Санкт-Петербург'],
        'city_filter': None,
        'sort_by': 'date',
        'current_page': 0
    }

    await handle_city_selection(mock_callback, user_results)

    mock_callback.answer.assert_called()

@pytest.mark.asyncio
async def test_handle_sort(mock_callback, user_results):
    user_results[12345] = {
        'concerts': [{'title': 'Concert 1'}, {'title': 'Concert 2'}],
        'original_concerts': [{'title': 'Concert 1'}, {'title': 'Concert 2'}],
        'available_cities': [],
        'city_filter': None,
        'sort_by': 'date',
        'current_page': 0
    }
    mock_callback.data = "sort_artist"

    await handle_sort(mock_callback, user_results)

    mock_callback.answer.assert_called()

@pytest.mark.asyncio
async def test_handle_pagination(mock_callback, user_results):
    user_results[12345] = {
        'concerts': [{'title': f'Concert {i}'} for i in range(20)],
        'original_concerts': [{'title': f'Concert {i}'} for i in range(20)],
        'available_cities': [],
        'city_filter': None,
        'sort_by': 'date',
        'current_page': 0
    }
    mock_callback.data = "page_1"

    await handle_pagination(mock_callback, user_results)

    mock_callback.answer.assert_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.callback_handler.RecommendationService')
@patch('src.bot.handlers.callback_handler.ConcertRepository')
async def test_handle_recommendations(mock_repo, mock_rec_service, mock_callback, user_results):
    user_results[12345] = {
        'concerts': [],
        'original_concerts': [],
        'artists': ['Artist 1', 'Artist 2'],
        'available_cities': [],
        'city_filter': None,
        'sort_by': 'date',
        'current_page': 0
    }

    mock_service_instance = MagicMock()
    mock_service_instance.enabled = True
    mock_service_instance.get_recommendations = AsyncMock(return_value=[])
    mock_rec_service.return_value = mock_service_instance

    mock_repo_instance = MagicMock()
    mock_repo_instance.close = AsyncMock()
    mock_repo.return_value = mock_repo_instance

    await handle_recommendations(mock_callback, user_results)

    mock_callback.answer.assert_called()

def test_concert_service_initialization():
    mock_repo = MagicMock()
    service = ConcertService(mock_repo)

    assert service.repository == mock_repo
    assert service.matcher is not None

