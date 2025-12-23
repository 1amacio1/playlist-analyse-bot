import pytest
from unittest.mock import Mock
from src.services.concert_service import ConcertMatcherService

@pytest.fixture
def repo():
    r = Mock()
    r.get_events_by_category.return_value = []
    return r

@pytest.fixture
def service(repo):
    return ConcertMatcherService(repo, city='moscow')

def test_normalize(service):
    res = service.normalize_name('  Test  Name  ')
    assert res == 'test name'

def test_stop_word(service):
    assert service.is_stop_word('в') is True
    assert service.is_stop_word('test') is False

def test_find_artist(service):
    res = service.find_artist_in_text('Artist', 'Concert by Artist')
    assert res is True

def test_find_artist_short(service):
    res = service.find_artist_in_text('AB', 'AB concert')
    assert res is False

def test_find_concerts(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'Artist Name Concert', 'full_title': '', 'description': ''}
    ]
    res = service.find_concerts_for_artists(['Artist Name'])
    assert 'Artist Name' in res

def test_find_concerts_full_title(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'C', 'full_title': 'Test Artist Concert', 'description': ''}
    ]
    res = service.find_concerts_for_artists(['Test Artist'])
    assert 'Test Artist' in res
    assert len(res['Test Artist']) > 0

def test_find_concerts_desc(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'C', 'full_title': '', 'description': 'Concert by Test Artist'}
    ]
    res = service.find_concerts_for_artists(['Test Artist'])
    assert 'Test Artist' in res
    assert len(res['Test Artist']) > 0

def test_get_all(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'Test Artist Name Concert', 'full_title': '', 'description': ''},
        {'url': 'https://afisha.yandex.ru/moscow/2', 'title': 'Other Concert', 'full_title': '', 'description': ''}
    ]
    res = service.get_all_matching_concerts(['Test Artist Name'])
    assert len(res) >= 1

def test_city_check(service):
    c = {'url': 'https://afisha.yandex.ru/moscow/event'}
    res = service.is_from_city(c)
    assert res is True

def test_city_check_no_url(service):
    c = {}
    res = service.is_from_city(c)
    assert res is False

def test_find_artist_empty(service):
    res = service.find_artist_in_text('', 'text')
    assert res is False

def test_find_artist_one_word(service):
    res = service.find_artist_in_text('Test', 'Test concert')
    assert res is True

def test_find_artist_two_words(service):
    res = service.find_artist_in_text('Test Artist', 'Concert by Test Artist')
    assert res is True

def test_normalize_empty(service):
    res = service.normalize_name('')
    assert res == ''

def test_normalize_special(service):
    res = service.normalize_name('  Test   Name  ')
    assert res == 'test name'

def test_find_artist_one_word_long(service):
    res = service.find_artist_in_text('TestArtist', 'Concert by TestArtist')
    assert res is True

def test_find_artist_three_words(service):
    res = service.find_artist_in_text('Test Artist Name', 'Concert by Test Artist Name')
    assert res is True

def test_find_concerts_empty(service, repo):
    repo.get_events_by_category.return_value = []
    res = service.find_concerts_for_artists(['Artist'])
    assert res == {}

def test_get_all_empty(service, repo):
    repo.get_events_by_category.return_value = []
    res = service.get_all_matching_concerts(['Artist'])
    assert res == []

def test_find_concerts_no_match(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'Other Concert', 'full_title': '', 'description': ''}
    ]
    res = service.find_concerts_for_artists(['Test Artist'])
    assert 'Test Artist' not in res

def test_find_concerts_wrong_city(service, repo):
    repo.get_events_by_category.return_value = [
        {'url': 'https://afisha.yandex.ru/spb/1', 'title': 'Test Artist Concert', 'full_title': '', 'description': ''}
    ]
    res = service.find_concerts_for_artists(['Test Artist'])
    assert 'Test Artist' not in res
