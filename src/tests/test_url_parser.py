
import pytest
from src.utils.url_parser import extract_from_url

class TestExtractFromUrl:
    
    
    def test_extract_from_iframe(self):
        

        html = '<iframe src="https://music.yandex.ru/iframe/playlist/user123/456789"></iframe>'
        owner, kind = extract_from_url(html)
        assert owner == 'user123'
        assert kind == '456789'
    
    def test_extract_from_iframe_with_quotes(self):
        
        html = "<iframe src='https://music.yandex.ru/iframe/playlist/user123/456789'></iframe>"
        owner, kind = extract_from_url(html)
        assert owner == 'user123'
        assert kind == '456789'
    
    def test_extract_from_mobile_url(self):
        
        url = 'https://music.yandex.ru/users/user123/playlists/456789'
        owner, kind = extract_from_url(url)
        assert owner == 'user123'
        assert kind == '456789'
    
    def test_extract_from_iframe_url(self):
        

        url = 'https://music.yandex.ru/iframe/playlist/user123/456789'
        owner, kind = extract_from_url(url)
        assert owner == 'user123'
        assert kind == '456789'
    
    def test_invalid_url_raises_error(self):
        
        with pytest.raises(ValueError, match="URL не подходит"):
            extract_from_url('https://example.com/invalid')
    
    def test_empty_string_raises_error(self):
        
        with pytest.raises(ValueError):
            extract_from_url('')
    
    def test_whitespace_handling(self):
        
        url = '  https://music.yandex.ru/users/user123/playlists/456789  '
        owner, kind = extract_from_url(url)
        assert owner == 'user123'
        assert kind == '456789'

