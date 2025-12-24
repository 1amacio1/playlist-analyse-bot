
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError:

    InlineKeyboardMarkup = type('InlineKeyboardMarkup', (), {})
    InlineKeyboardButton = type('InlineKeyboardButton', (), {})

from bot.utils import (
    remove_duplicate_concerts,
    get_available_cities,
    filter_by_city,
    group_by_artist,
    extract_date_sort_key,
    format_concert_date_time,
    format_concert_message,
    create_city_selection_keyboard,
    create_concert_keyboard
)

class TestRemoveDuplicateConcerts:
    
    
    def test_remove_duplicates_by_url(self):
        
        concerts = [
            {'url': 'https://example.com/concert1', 'title': 'Concert 1'},
            {'url': 'https://example.com/concert1?param=value', 'title': 'Concert 1 Duplicate'},
            {'url': 'https://example.com/concert2', 'title': 'Concert 2'},
        ]
        result = remove_duplicate_concerts(concerts)
        assert len(result) == 2
        assert result[0]['title'] == 'Concert 1'
        assert result[1]['title'] == 'Concert 2'
    
    def test_remove_duplicates_with_trailing_slash(self):
        
        concerts = [
            {'url': 'https://example.com/concert1/', 'title': 'Concert 1'},
            {'url': 'https://example.com/concert1', 'title': 'Concert 1 Duplicate'},
        ]
        result = remove_duplicate_concerts(concerts)
        assert len(result) == 1
    
    def test_keep_concerts_without_url(self):
        
        concerts = [
            {'url': '', 'title': 'Concert 1'},
            {'title': 'Concert 2'},
        ]
        result = remove_duplicate_concerts(concerts)
        assert len(result) == 2
    
    def test_handle_none_and_invalid(self):
        
        concerts = [
            {'url': 'https://example.com/concert1', 'title': 'Concert 1'},
            None,
            {'title': 'Concert 2'},
            'invalid',
        ]
        result = remove_duplicate_concerts(concerts)
        assert len(result) >= 1
        assert all(isinstance(concert, dict) for concert in result)

class TestGetAvailableCities:
    
    
    def test_extract_cities_from_url(self):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1'},
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2'},
            {'url': 'https://afisha.yandex.ru/moscow/concert3'},
        ]
        result = get_available_cities(concerts)
        assert 'Москва' in result
        assert 'Санкт-Петербург' in result
        assert len(result) == 2
    
    def test_extract_cities_from_city_field(self):
        
        concerts = [
            {'city': 'Москва', 'url': ''},
            {'city': 'Санкт-Петербург', 'url': ''},
            {'city': 'Екатеринбург', 'url': ''},
        ]
        result = get_available_cities(concerts)
        assert 'Москва' in result
        assert 'Санкт-Петербург' in result
        assert 'Екатеринбург' in result
    
    def test_extract_cities_from_description(self):
        
        
        concerts = [
            {'description': 'Концерт в москва', 'url': '', 'city': ''},
            {'description': 'Событие в санкт-петербург', 'url': '', 'city': ''},
        ]
        result = get_available_cities(concerts)

        assert 'Москва' in result
        assert 'Санкт-Петербург' in result
    
    def test_extract_cities_from_venue(self):
        

        concerts = [
            {'venue': 'Клуб в москва', 'url': '', 'city': ''},
            {'venue': 'Театр в спб', 'url': '', 'city': ''},
        ]
        result = get_available_cities(concerts)

        assert 'Москва' in result
        assert 'Санкт-Петербург' in result
    
    def test_empty_list(self):
        
        result = get_available_cities([])
        assert result == []
    
    def test_no_cities_found(self):
        
        concerts = [
            {'url': 'https://example.com/concert1', 'title': 'Concert 1'},
        ]
        result = get_available_cities(concerts)
        assert result == []

class TestFilterByCity:
    
    
    def test_filter_by_moscow(self):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Moscow Concert'},
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2', 'title': 'SPB Concert'},
            {'city': 'Москва', 'url': '', 'title': 'Moscow Concert 2'},
        ]
        result = filter_by_city(concerts, 'Москва')
        assert len(result) == 2
        assert all('Moscow' in concert['title'] for concert in result)
    
    def test_filter_by_description(self):
        

        concerts = [
            {'description': 'Концерт в москва', 'url': '', 'title': 'Concert 1', 'city': ''},
            {'description': 'Событие в санкт-петербург', 'url': '', 'title': 'Concert 2', 'city': ''},
        ]
        result = filter_by_city(concerts, 'Москва')

        assert len(result) == 1
        assert result[0]['title'] == 'Concert 1'
    
    def test_filter_removes_duplicates(self):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Concert 1'},
            {'url': 'https://afisha.yandex.ru/moscow/concert1?param=value', 'title': 'Concert 1'},
        ]
        result = filter_by_city(concerts, 'Москва')
        assert len(result) == 1
    
    def test_empty_result(self):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert1', 'title': 'SPB Concert'},
        ]
        result = filter_by_city(concerts, 'Москва')
        assert result == []

class TestGroupByArtist:
    
    
    def test_group_concerts_by_artist(self):
        
        concerts = [
            {'matched_artist': 'Artist 1', 'title': 'Concert 1'},
            {'matched_artist': 'Artist 1', 'title': 'Concert 2'},
            {'matched_artist': 'Artist 2', 'title': 'Concert 3'},
        ]
        result = group_by_artist(concerts)
        assert 'Artist 1' in result
        assert 'Artist 2' in result
        assert len(result['Artist 1']) == 2
        assert len(result['Artist 2']) == 1
    
    def test_unknown_artist(self):
        
        concerts = [
            {'title': 'Concert 1'},
            {'matched_artist': 'Artist 1', 'title': 'Concert 2'},
        ]
        result = group_by_artist(concerts)
        assert 'Неизвестный артист' in result
        assert len(result['Неизвестный артист']) == 1

class TestExtractDateSortKey:
    
    
    def test_iso_format(self):
        
        result = extract_date_sort_key('2024-03-15')
        assert result == (2024, 3, 15)
    
    def test_dd_mm_yyyy_format(self):
        
        result = extract_date_sort_key('15.03.2024')
        assert result == (2024, 3, 15)
    
    def test_russian_month_format(self):
        
        result = extract_date_sort_key('15 марта 2024')
        assert result == (2024, 3, 15)
    
    def test_empty_date(self):
        
        result = extract_date_sort_key('')
        assert result == (9999, 12, 31)
    
    def test_invalid_date(self):
        
        result = extract_date_sort_key('invalid date')
        assert result == (9999, 12, 31)

class TestFormatConcertDateTime:
    
    
    def test_format_with_date_and_time(self):
        
        concert = {
            'dates': ['2024-03-15'],
            'desc': '15 марта 2024, 19:00'
        }
        result = format_concert_date_time(concert)
        assert '15 марта' in result or 'марта' in result
    
    def test_format_without_time(self):
        
        concert = {
            'dates': ['2024-03-15']
        }
        result = format_concert_date_time(concert)
        assert result != 'Дата не указана'
    
    def test_no_date(self):
        
        concert = {}
        result = format_concert_date_time(concert)
        assert result == 'Дата не указана'

class TestFormatConcertMessage:
    
    
    def test_format_empty_list(self):
        
        result = format_concert_message([], 0, 10, 'date')
        assert 'не найдены' in result
    
    def test_format_with_concerts(self):
        
        concerts = [
            {
                'title': 'Test Concert',
                'dates': ['2024-03-15'],
                'venue': 'Test Venue',
                'url': 'https://example.com'
            }
        ]
        result = format_concert_message(concerts, 0, 10, 'date')
        assert 'Test Concert' in result
        assert 'Test Venue' in result
    
    def test_pagination(self):
        
        concerts = [
            {'title': f'Concert {i}', 'dates': ['2024-03-15'], 'venue': 'Venue'}
            for i in range(15)
        ]
        result = format_concert_message(concerts, 0, 10, 'date')
        assert 'Показано 1-10' in result
    
    def test_remove_duplicates_in_message(self):
        
        concerts = [
            {'url': 'https://example.com/concert1', 'title': 'Concert 1'},
            {'url': 'https://example.com/concert1?param=value', 'title': 'Concert 1'},
        ]
        result = format_concert_message(concerts, 0, 10, 'date')

        assert result.count('Concert 1') == 1

class TestCreateCitySelectionKeyboard:
    
    
    def test_create_keyboard(self):
        
        cities = ['Москва', 'Санкт-Петербург', 'Екатеринбург']
        keyboard = create_city_selection_keyboard(cities)
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0
    
    def test_empty_cities(self):
        
        keyboard = create_city_selection_keyboard([])
        assert isinstance(keyboard, InlineKeyboardMarkup)

        assert len(keyboard.inline_keyboard) == 1
    
    def test_single_city(self):
        
        keyboard = create_city_selection_keyboard(['Москва'])
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 1

class TestCreateConcertKeyboard:
    
    
    def test_create_keyboard(self):
        
        concerts = [
            {'title': 'Concert 1', 'url': 'https://example.com'}
        ]
        keyboard = create_concert_keyboard(concerts, 0, 10, None, 'date', [])
        assert isinstance(keyboard, InlineKeyboardMarkup)
    
    def test_pagination_buttons(self):
        
        concerts = [
            {'title': f'Concert {i}', 'url': 'https://example.com'}
            for i in range(25)
        ]
        keyboard = create_concert_keyboard(concerts, 0, 10, None, 'date', [])

        buttons_text = [
            btn.text for row in keyboard.inline_keyboard
            for btn in row
        ]
        assert 'Вперед ▶️' in buttons_text
    
    def test_city_filter_buttons(self):
        
        concerts = [
            {'title': 'Concert 1', 'url': 'https://example.com'}
        ]
        keyboard = create_concert_keyboard(
            concerts, 0, 10, 'Москва', 'date', ['Москва', 'Санкт-Петербург']
        )
        buttons_text = [
            btn.text for row in keyboard.inline_keyboard
            for btn in row
        ]
        assert '📍 Москва' in buttons_text or '🌍 Все города' in buttons_text
    
    def test_sort_buttons(self):
        
        concerts = [
            {'title': 'Concert 1', 'url': 'https://example.com'}
        ]
        keyboard = create_concert_keyboard(concerts, 0, 10, None, 'date', [])
        buttons_text = [
            btn.text for row in keyboard.inline_keyboard
            for btn in row
        ]
        assert '👤 По артисту' in buttons_text

