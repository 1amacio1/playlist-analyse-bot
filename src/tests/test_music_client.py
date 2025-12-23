import pytest
from unittest.mock import Mock, patch
from src.services.music_playlist_client import MusicClient

@patch('src.services.music_playlist_client.Client')
def test_init(mock_client):
    mc = Mock()
    mc.init.return_value = mc
    mock_client.return_value = mc
    c = MusicClient('token')
    assert c is not None

@patch('src.services.music_playlist_client.Client')
@patch('src.services.music_playlist_client.os.getenv')
def test_from_env(mock_getenv, mock_client):
    mock_getenv.return_value = 'token'
    mc = Mock()
    mc.init.return_value = mc
    mock_client.return_value = mc
    c = MusicClient.from_env()
    assert c is not None

@patch('src.services.music_playlist_client.os.getenv')
def test_no_token(mock_getenv):
    mock_getenv.return_value = None
    with pytest.raises(EnvironmentError):
        MusicClient.from_env()

