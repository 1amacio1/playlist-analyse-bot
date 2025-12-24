
import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from aiogram.types import CallbackQuery, User, Message
except ImportError:

    CallbackQuery = type('CallbackQuery', (), {})
    User = type('User', (), {})
    Message = type('Message', (), {})

from bot.handlers.callback_handler import (
    handle_city_selection,
    handle_sort,
    handle_pagination,
    handle_reminder,
    handle_recommendations,
    handle_refresh
)

class TestHandleCitySelection:
    
    
    @pytest.fixture
    def mock_callback(self):
        
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 12345
        callback.data = 'city_moscow'
        callback.message = Mock(spec=Message)
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def user_results(self):
        
        return {
            12345: {
                'concerts': [
                    {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Concert 1'},
                    {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2', 'title': 'Concert 2'},
                ],
                'original_concerts': [
                    {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Concert 1'},
                    {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2', 'title': 'Concert 2'},
                ],
                'city_filter': None,
                'sort_by': 'date',
                'current_page': 0,
                'available_cities': ['Москва', 'Санкт-Петербург']
            }
        }
    
    @pytest.mark.asyncio
    async def test_select_city(self, mock_callback, user_results):
        
        mock_callback.data = 'city_Москва'
        
        await handle_city_selection(mock_callback, user_results)
        
        assert user_results[12345]['city_filter'] == 'Москва'
        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_select_all_cities(self, mock_callback, user_results):
        
        mock_callback.data = 'city_all'
        
        await handle_city_selection(mock_callback, user_results)
        
        assert user_results[12345]['city_filter'] is None
        mock_callback.message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_callback, user_results):
        
        mock_callback.from_user.id = 99999
        
        await handle_city_selection(mock_callback, user_results)
        
        mock_callback.answer.assert_called_once()
        answer_text = mock_callback.answer.call_args[0][0]
        assert 'устарели' in answer_text or 'заново' in answer_text

class TestHandleSort:
    
    
    @pytest.fixture
    def mock_callback(self):
        
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 12345
        callback.data = 'sort_artist'
        callback.message = Mock(spec=Message)
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def user_results(self):
        
        return {
            12345: {
                'concerts': [
                    {'matched_artist': 'Artist 2', 'title': 'Concert 2'},
                    {'matched_artist': 'Artist 1', 'title': 'Concert 1'},
                ],
                'city_filter': None,
                'sort_by': 'date',
                'current_page': 0
            }
        }
    
    @pytest.mark.asyncio
    async def test_sort_by_artist(self, mock_callback, user_results):
        
        mock_callback.data = 'sort_artist'
        
        await handle_sort(mock_callback, user_results)
        
        assert user_results[12345]['sort_by'] == 'artist'
        mock_callback.message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sort_by_date(self, mock_callback, user_results):
        
        mock_callback.data = 'sort_date'
        user_results[12345]['sort_by'] = 'artist'
        
        await handle_sort(mock_callback, user_results)
        
        assert user_results[12345]['sort_by'] == 'date'
        mock_callback.message.edit_text.assert_called_once()

class TestHandlePagination:
    
    
    @pytest.fixture
    def mock_callback(self):
        
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 12345
        callback.data = 'page_1'
        callback.message = Mock(spec=Message)
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def user_results(self):
        
        return {
            12345: {
                'concerts': [
                    {'title': f'Concert {i}'} for i in range(25)
                ],
                'sort_by': 'date',
                'current_page': 0
            }
        }
    

class TestHandleReminder:
    
    
    @pytest.fixture
    def mock_callback(self):
        
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 12345
        callback.data = 'remind_0'
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def user_results(self):
        
        return {
            12345: {
                'concerts': [
                    {
                        'title': 'Test Concert',
                        'dates': ['2024-03-15'],
                        'venue': 'Test Venue'
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_add_reminder(self, mock_callback, user_results):
        
        await handle_reminder(mock_callback, user_results)
        
        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args[1]
        assert call_kwargs.get('show_alert', False) is True
    
    @pytest.mark.asyncio
    async def test_reminder_invalid_index(self, mock_callback, user_results):
        
        mock_callback.data = 'remind_999'
        
        await handle_reminder(mock_callback, user_results)
        
        mock_callback.answer.assert_called_once()
        answer_text = mock_callback.answer.call_args[0][0]
        assert 'не найден' in answer_text or 'Ошибка' in answer_text

class TestHandleRefresh:
    
    
    @pytest.fixture
    def mock_callback(self):
        
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 12345
        callback.answer = AsyncMock()
        callback.message = Mock(spec=Message)
        callback.message.edit_text = AsyncMock()
        return callback
    
    @pytest.fixture
    def user_results(self):
        
        return {
            12345: {
                'concerts': [
                    {'title': 'Concert 1'},
                    {'title': 'Concert 2'},
                ],
                'sort_by': 'date',
                'current_page': 0
            }
        }
    

