"""Тесты для src/services/music_playlist_client.py"""
import pytest
from unittest.mock import Mock, patch
from src.services.music_playlist_client import MusicClient


class TestMusicClient:
    """Тесты для класса MusicClient"""
    
    @patch('src.services.music_playlist_client.Client')
    def test_init(self, mock_client_class):
        """Тест инициализации клиента"""
        mock_client = Mock()
        mock_client.init.return_value = mock_client
        mock_client_class.return_value = mock_client
        
        client = MusicClient('test_token')
        mock_client_class.assert_called_once_with('test_token')
        mock_client.init.assert_called_once()
    
    @patch('src.services.music_playlist_client.Client')
    @patch('src.services.music_playlist_client.os.getenv')
    def test_from_env_success(self, mock_getenv, mock_client_class):
        """Тест создания клиента из переменной окружения"""
        mock_getenv.return_value = 'test_token'
        mock_client = Mock()
        mock_client.init.return_value = mock_client
        mock_client_class.return_value = mock_client
        
        client = MusicClient.from_env()
        mock_getenv.assert_called_once_with('YANDEX_MUSIC_TOKEN')
        assert client is not None
    
    @patch('src.services.music_playlist_client.os.getenv')
    def test_from_env_no_token(self, mock_getenv):
        """Тест создания клиента без токена"""
        mock_getenv.return_value = None
        
        with pytest.raises(EnvironmentError, match="YANDEX_MUSIC_TOKEN не установлен"):
            MusicClient.from_env()
    
    @patch('src.services.music_playlist_client.Client')
    def test_get_playlist(self, mock_client_class):
        """Тест получения плейлиста"""
        mock_client = Mock()
        mock_client.init.return_value = mock_client
        mock_client.users_playlists.return_value = Mock()
        mock_client_class.return_value = mock_client
        
        client = MusicClient('test_token')
        playlist = client.get_playlist('kind123', 'owner123')
        
        mock_client.users_playlists.assert_called_once_with('kind123', 'owner123')
        assert playlist is not None

