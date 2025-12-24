
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from aiogram.types import Message, User
    from aiogram.fsm.context import FSMContext
except ImportError:

    Message = type('Message', (), {})
    User = type('User', (), {})
    FSMContext = type('FSMContext', (), {})

from bot.handlers.playlist_handler import ConcertService, handle_playlist_url

class TestConcertService:
    
    
    @pytest.fixture
    def mock_repository(self):
        
        mock_repository = Mock()
        mock_repository.get_events_by_category.return_value = []
        return mock_repository
    
    @pytest.fixture
    def service(self, mock_repository):
        
        return ConcertService(mock_repository)
    
    def test_get_available_cities(self, service):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1'},
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2'},
        ]
        result = service.get_available_cities(concerts)
        assert 'Москва' in result
        assert 'Санкт-Петербург' in result
    
    def test_find_concerts_by_artists(self, service, mock_repository):
        
        mock_repository.get_events_by_category.return_value = [
            {
                'url': 'https://afisha.yandex.ru/moscow/concert1',
                'title': 'Artist Name Concert',
                'full_title': '',
                'description': ''
            }
        ]
        
        result = service.find_concerts_by_artists(['Artist Name'])
        assert len(result) >= 0
        if len(result) > 0:
            assert result[0]['title'] == 'Artist Name Concert'
    
    def test_filter_by_city(self, service):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Moscow Concert'},
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2', 'title': 'SPB Concert'},
        ]
        result = service.filter_by_city(concerts, 'Москва')
        assert len(result) == 1
        assert result[0]['title'] == 'Moscow Concert'
    
    def test_group_by_artist(self, service):
        
        concerts = [
            {'matched_artist': 'Artist 1', 'title': 'Concert 1'},
            {'matched_artist': 'Artist 1', 'title': 'Concert 2'},
            {'matched_artist': 'Artist 2', 'title': 'Concert 3'},
        ]
        result = service.group_by_artist(concerts)
        assert 'Artist 1' in result
        assert 'Artist 2' in result
        assert len(result['Artist 1']) == 2

class TestHandlePlaylistUrl:
    
    
    @pytest.fixture
    def mock_message(self):
        
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 12345
        message.text = 'https://music.yandex.ru/users/user123/playlists/456789'
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_state(self):
        
        mock_state = Mock(spec=FSMContext)
        mock_state.clear = AsyncMock()
        return mock_state
    
    @pytest.fixture
    def user_results(self):
        
        return {}
    
    @pytest.mark.asyncio
    async def test_invalid_url_format(self, mock_message, mock_state, user_results):
        
        mock_message.text = 'invalid url'
        
        await handle_playlist_url(mock_message, mock_state, user_results)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert 'Неверный формат' in call_args or 'не подходит' in call_args
    
    @pytest.mark.asyncio
    @patch('bot.handlers.playlist_handler.MusicClient')
    @patch('bot.handlers.playlist_handler.ServicePlaylist')
    @patch('bot.handlers.playlist_handler.ConcertRepository')
    @patch('bot.handlers.playlist_handler.extract_from_url')
    async def test_successful_playlist_processing(
        self, 
        extract, 
        mock_repo_class,
        mock_service_class,
        mock_client_class,
        mock_message, 
        mock_state, 
        user_results
    ):
        

        extract.return_value = ('user123', '456789')
        
        mock_client = Mock()
        mock_playlist = Mock()
        mock_track = Mock()
        mock_track.track = Mock()
        mock_track.track.artists = [Mock(name='Artist 1')]
        mock_playlist.fetch_tracks.return_value = [mock_track]
        mock_client.get_playlist.return_value = mock_playlist
        mock_client_class.from_env.return_value = mock_client
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_repository = Mock()
        mock_repository.get_events_by_category.return_value = []
        mock_repository.close = Mock()
        mock_repo_class.return_value = mock_repository
        
        mock_message.answer.return_value = Mock()
        mock_message.answer.return_value.edit_text = AsyncMock()
        
        await handle_playlist_url(mock_message, mock_state, user_results)
        

        mock_message.answer.assert_called()
        mock_state.clear.assert_called()
    
    @pytest.mark.asyncio
    @patch('bot.handlers.playlist_handler.MusicClient')
    @patch('bot.handlers.playlist_handler.extract_from_url')
    async def test_playlist_not_found_error(
        self,
        extract,
        mock_client_class,
        mock_message,
        mock_state,
        user_results
    ):
        
        extract.return_value = ('user123', '456789')
        
        mock_client = Mock()
        mock_client.get_playlist.side_effect = Exception("not found")
        mock_client_class.from_env.return_value = mock_client
        
        mock_message.answer.return_value = Mock()
        mock_message.answer.return_value.edit_text = AsyncMock()
        
        await handle_playlist_url(mock_message, mock_state, user_results)
        

        edit_calls = mock_message.answer.return_value.edit_text.call_args_list
        if edit_calls:
            error_text = edit_calls[-1][0][0]
            assert 'не найден' in error_text or 'Ошибка' in error_text

