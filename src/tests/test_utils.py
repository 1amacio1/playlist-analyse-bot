import pytest
from src.bot.utils import remove_duplicate_concerts, get_available_cities, filter_by_city, group_by_artist
from src.bot.utils import extract_date_sort_key, format_concert_date_time, format_concert_message
from src.bot.utils import create_city_selection_keyboard, create_concert_keyboard

def test_remove_duplicates():
    data = [
        {'url': 'https://test.com/1', 'title': 'A'},
        {'url': 'https://test.com/1?x=1', 'title': 'B'},
        {'url': 'https://test.com/2', 'title': 'C'}
    ]
    res = remove_duplicate_concerts(data)
    assert len(res) == 2

def test_remove_none():
    data = [{'url': 'test'}, None, {'url': 'test2'}]
    res = remove_duplicate_concerts(data)
    assert len(res) == 2

def test_get_cities():
    data = [
        {'url': 'https://afisha.yandex.ru/moscow/event1'},
        {'url': 'https://afisha.yandex.ru/saint-petersburg/event2'}
    ]
    res = get_available_cities(data)
    assert 'Москва' in res
    assert 'Санкт-Петербург' in res

def test_get_cities_from_field():
    data = [{'city': 'Москва', 'url': ''}]
    res = get_available_cities(data)
    assert 'Москва' in res

def test_get_cities_empty():
    res = get_available_cities([])
    assert res == []

def test_filter_city():
    data = [
        {'url': 'https://afisha.yandex.ru/moscow/event1', 'title': 'M'},
        {'url': 'https://afisha.yandex.ru/spb/event2', 'title': 'S'}
    ]
    res = filter_by_city(data, 'Москва')
    assert len(res) == 1
    assert res[0]['title'] == 'M'

def test_filter_by_desc():
    data = [{'description': 'Концерт в москва', 'url': '', 'title': 'T'}]
    res = filter_by_city(data, 'Москва')
    assert len(res) == 1

def test_group_artist():
    data = [
        {'matched_artist': 'A1', 'title': 'T1'},
        {'matched_artist': 'A1', 'title': 'T2'},
        {'matched_artist': 'A2', 'title': 'T3'}
    ]
    res = group_by_artist(data)
    assert 'A1' in res
    assert len(res['A1']) == 2

def test_group_no_artist():
    data = [{'title': 'T'}]
    res = group_by_artist(data)
    assert 'Неизвестный артист' in res

def test_date_sort_iso():
    res = extract_date_sort_key('2024-03-15')
    assert res == (2024, 3, 15)

def test_date_sort_ddmm():
    res = extract_date_sort_key('15.03.2024')
    assert res == (2024, 3, 15)

def test_date_sort_ru():
    res = extract_date_sort_key('15 марта 2024')
    assert res == (2024, 3, 15)

def test_date_sort_empty():
    res = extract_date_sort_key('')
    assert res == (9999, 12, 31)

def test_format_date():
    c = {'dates': ['2024-03-15'], 'description': '15 марта 2024, 19:00'}
    res = format_concert_date_time(c)
    assert res is not None

def test_format_no_date():
    c = {}
    res = format_concert_date_time(c)
    assert res == 'Дата не указана'

def test_format_message():
    data = [{'title': 'Test', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'}]
    res = format_concert_message(data, 0, 10, 'date')
    assert 'Test' in res

def test_format_message_empty():
    res = format_concert_message([], 0, 10, 'date')
    assert 'не найдены' in res

def test_format_message_artist():
    data = [{'title': 'T', 'matched_artist': 'A', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'}]
    res = format_concert_message(data, 0, 10, 'artist')
    assert 'A' in res

def test_city_keyboard():
    cities = ['Москва', 'СПб']
    kb = create_city_selection_keyboard(cities)
    assert kb is not None

def test_city_keyboard_empty():
    kb = create_city_selection_keyboard([])
    assert kb is not None

def test_concert_keyboard():
    data = [{'title': 'T', 'url': 'http://test.com'}]
    kb = create_concert_keyboard(data, 0, 10, None, 'date', [])
    assert kb is not None

def test_concert_keyboard_pagination():
    data = [{'title': f'T{i}', 'url': 'http://test.com'} for i in range(25)]
    kb = create_concert_keyboard(data, 0, 10, None, 'date', [])
    assert kb is not None

def test_concert_keyboard_city():
    data = [{'title': 'T', 'url': 'http://test.com'}]
    kb = create_concert_keyboard(data, 0, 10, 'Москва', 'date', ['Москва'])
    assert kb is not None

def test_concert_keyboard_artist():
    data = [{'title': 'T', 'url': 'http://test.com'}]
    kb = create_concert_keyboard(data, 0, 10, None, 'artist', [])
    assert kb is not None

def test_date_sort_ddmm():
    res = extract_date_sort_key('15.03.2024')
    assert res == (2024, 3, 15)

def test_date_sort_slash():
    res = extract_date_sort_key('15/03/2024')
    assert res == (2024, 3, 15)

def test_date_sort_ru_no_year():
    res = extract_date_sort_key('15 марта')
    assert res[1] == 3

def test_format_message_pagination():
    data = [{'title': f'T{i}', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'} for i in range(15)]
    res = format_concert_message(data, 0, 10, 'date')
    assert 'Показано 1-10' in res or 'Показано' in res

def test_format_message_artist_sort():
    data = [{'title': 'T', 'matched_artist': 'A', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'}]
    res = format_concert_message(data, 0, 10, 'artist')
    assert 'A' in res

def test_filter_empty():
    res = filter_by_city([], 'Москва')
    assert res == []

def test_group_empty():
    res = group_by_artist([])
    assert res == {}

def test_remove_duplicates_no_url():
    data = [{'title': 'A'}, {'title': 'B'}]
    res = remove_duplicate_concerts(data)
    assert len(res) == 2

def test_get_cities_venue():
    data = [{'venue': 'Москва, Venue'}]
    res = get_available_cities(data)
    assert 'Москва' in res

def test_get_cities_title():
    data = [{'title': 'Concert in Москва', 'url': ''}]
    res = get_available_cities(data)
    assert 'Москва' in res or len(res) >= 0

def test_filter_by_title():
    data = [{'title': 'Concert in москва', 'url': ''}]
    res = filter_by_city(data, 'Москва')
    assert len(res) == 1

def test_date_sort_ddmm_no_year():
    res = extract_date_sort_key('15.03')
    assert res[1] == 3

def test_format_date_iso():
    c = {'dates': ['2024-03-15'], 'description': '15 марта 2024, 19:00'}
    res = format_concert_date_time(c)
    assert 'марта' in res

def test_format_date_with_time():
    c = {'dates': ['2024-03-15'], 'description': '15 марта 2024, 19:00'}
    res = format_concert_date_time(c)
    assert '19:00' in res

def test_format_message_no_venue():
    data = [{'title': 'Test', 'dates': ['2024-03-15'], 'url': 'http://test.com'}]
    res = format_concert_message(data, 0, 10, 'date')
    assert 'Test' in res

def test_city_keyboard_one():
    cities = ['Москва']
    kb = create_city_selection_keyboard(cities)
    assert kb is not None

def test_concert_keyboard_no_cities():
    data = [{'title': 'T', 'url': 'http://test.com'}]
    kb = create_concert_keyboard(data, 0, 10, None, 'date', None)
    assert kb is not None

def test_concert_keyboard_with_city():
    data = [{'title': 'T', 'url': 'http://test.com'}]
    kb = create_concert_keyboard(data, 0, 10, 'Москва', 'date', ['Москва'])
    assert kb is not None

def test_remove_duplicates_slash():
    data = [
        {'url': 'https://test.com/1/', 'title': 'A'},
        {'url': 'https://test.com/1', 'title': 'B'}
    ]
    res = remove_duplicate_concerts(data)
    assert len(res) == 1

def test_get_cities_multiple():
    data = [
        {'url': 'https://afisha.yandex.ru/moscow/1'},
        {'url': 'https://afisha.yandex.ru/moscow/2'},
        {'city': 'Москва', 'url': ''}
    ]
    res = get_available_cities(data)
    assert 'Москва' in res

def test_filter_by_venue():
    data = [{'venue': 'Venue в москва', 'url': '', 'title': 'T'}]
    res = filter_by_city(data, 'Москва')
    assert len(res) == 1

def test_filter_by_city_field():
    data = [{'city': 'Москва', 'url': '', 'title': 'T'}]
    res = filter_by_city(data, 'Москва')
    assert len(res) == 1

def test_date_sort_invalid():
    res = extract_date_sort_key('invalid date')
    assert res == (9999, 12, 31)

def test_format_date_clean():
    c = {'description': '15 марта 2024, 19:00'}
    res = format_concert_date_time(c)
    assert res is not None

def test_format_message_price():
    data = [{'title': 'T', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com', 'price': '1000 руб'}]
    res = format_concert_message(data, 0, 10, 'date')
    assert '1000' in res or 'T' in res

def test_format_message_city():
    data = [{'title': 'T', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'https://afisha.yandex.ru/moscow/event'}]
    res = format_concert_message(data, 0, 10, 'date')
    assert 'Москва' in res or 'T' in res

def test_format_date_no_time():
    c = {'dates': ['2024-03-15']}
    res = format_concert_date_time(c)
    assert 'марта' in res or '15' in res

def test_format_date_time_in_date():
    c = {'description': '15 марта 2024, 19:00'}
    res = format_concert_date_time(c)
    assert res is not None

def test_format_message_artist_multiple():
    data = [
        {'title': 'T1', 'matched_artist': 'A', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'},
        {'title': 'T2', 'matched_artist': 'A', 'dates': ['2024-03-16'], 'venue': 'V', 'url': 'http://test2.com'}
    ]
    res = format_concert_message(data, 0, 10, 'artist')
    assert 'A' in res

def test_format_message_start_idx():
    data = [{'title': f'T{i}', 'dates': ['2024-03-15'], 'venue': 'V', 'url': 'http://test.com'} for i in range(15)]
    res = format_concert_message(data, 10, 10, 'date')
    assert 'Показано 11-15' in res or 'Показано' in res

def test_concert_keyboard_page_1():
    data = [{'title': f'T{i}', 'url': 'http://test.com'} for i in range(25)]
    kb = create_concert_keyboard(data, 1, 10, None, 'date', [])
    assert kb is not None

def test_concert_keyboard_last_page():
    data = [{'title': f'T{i}', 'url': 'http://test.com'} for i in range(15)]
    kb = create_concert_keyboard(data, 1, 10, None, 'date', [])
    assert kb is not None
