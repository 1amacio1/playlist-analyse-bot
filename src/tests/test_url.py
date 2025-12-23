import pytest
from src.utils.url_parser import extract_from_url

def test_iframe():
    text = '<iframe src="https://music.yandex.ru/iframe/playlist/user123/456789"></iframe>'
    owner, kind = extract_from_url(text)
    assert owner == 'user123'
    assert kind == '456789'

def test_iframe_quotes():
    text = "<iframe src='https://music.yandex.ru/iframe/playlist/user123/456789'></iframe>"
    owner, kind = extract_from_url(text)
    assert owner == 'user123'
    assert kind == '456789'

def test_mobile():
    url = 'https://music.yandex.ru/users/user123/playlists/456789'
    owner, kind = extract_from_url(url)
    assert owner == 'user123'
    assert kind == '456789'

def test_error():
    with pytest.raises(ValueError):
        extract_from_url('bad url')

def test_empty():
    with pytest.raises(ValueError):
        extract_from_url('')

