import re
import logging
from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.concert_utils import get_concert_date, get_concert_time, get_concert_venue

logger = logging.getLogger(__name__)


def remove_duplicate_concerts(concerts: List[Dict]) -> List[Dict]:
    seen_urls = set()
    unique_concerts = []
    
    for concert in concerts:
        if concert is None or not isinstance(concert, dict):
            continue
            
        url = concert.get('url', '')
        if url:
            normalized_url = url.split('?')[0].rstrip('/')
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_concerts.append(concert)
        else:
            unique_concerts.append(concert)
    
    return unique_concerts


def get_available_cities(concerts: List[Dict]) -> List[str]:
    cities = set()
    city_codes = {
        'moscow': 'Москва',
        'saint-petersburg': 'Санкт-Петербург',
        'yekaterinburg': 'Екатеринбург',
        'novosibirsk': 'Новосибирск',
        'kazan': 'Казань',
        'nizhny-novgorod': 'Нижний Новгород',
        'chelyabinsk': 'Челябинск',
        'samara': 'Самара',
        'orenburg': 'Оренбург'
    }
    
    city_names_to_codes = {
        'москва': 'Москва',
        'санкт-петербург': 'Санкт-Петербург',
        'спб': 'Санкт-Петербург',
        'питер': 'Санкт-Петербург',
        'екатеринбург': 'Екатеринбург',
        'новосибирск': 'Новосибирск',
        'казань': 'Казань',
        'нижний новгород': 'Нижний Новгород',
        'челябинск': 'Челябинск',
        'самара': 'Самара',
        'оренбург': 'Оренбург'
    }
    
    cities_found = 0
    cities_not_found = 0
    
    for concert in concerts:
        city_found = False
        
        city_field = concert.get('city', '')
        if city_field and city_field != '-':
            city_lower = city_field.lower()
            for city_key, city_name in city_names_to_codes.items():
                if city_key in city_lower or city_lower in city_key:
                    cities.add(city_name)
                    cities_found += 1
                    city_found = True
                    break
            if not city_found:
                city_eng_mapping = {
                    'moscow': 'Москва',
                    'saint petersburg': 'Санкт-Петербург',
                    'st. petersburg': 'Санкт-Петербург',
                    'st petersburg': 'Санкт-Петербург',
                    'yekaterinburg': 'Екатеринбург',
                    'novosibirsk': 'Новосибирск',
                    'kazan': 'Казань',
                    'nizhny novgorod': 'Нижний Новгород',
                    'chelyabinsk': 'Челябинск',
                    'samara': 'Самара',
                    'orenburg': 'Оренбург'
                }
                for eng_name, city_name in city_eng_mapping.items():
                    if eng_name in city_lower:
                        cities.add(city_name)
                        cities_found += 1
                        city_found = True
                        break
        
        if not city_found:
            url = concert.get('url', '')
            if url:
                city_match = re.search(r'/(moscow|saint-petersburg|yekaterinburg|novosibirsk|kazan|nizhny-novgorod|chelyabinsk|samara|orenburg)/', url)
                if city_match:
                    city_code = city_match.group(1)
                    city_name = city_codes.get(city_code)
                    if city_name:
                        cities.add(city_name)
                        cities_found += 1
                        city_found = True
        
        if not city_found:
            description = concert.get('description', '')
            if description:
                desc_lower = description.lower()
                for city_key, city_name in city_names_to_codes.items():
                    if city_key in desc_lower:
                        cities.add(city_name)
                        cities_found += 1
                        city_found = True
                        break
        
        if not city_found:
            venue = concert.get('venue', '')
            if venue:
                venue_lower = venue.lower()
                for city_key, city_name in city_names_to_codes.items():
                    if city_key in venue_lower:
                        cities.add(city_name)
                        cities_found += 1
                        city_found = True
                        break
        
        if not city_found:
            cities_not_found += 1
            if cities_not_found <= 5:  # Логируем только первые 5 для отладки
                logger.debug(f"Город не найден для концерта: {concert.get('title', 'Unknown')[:50]}")
    
    logger.info(f"Извлечено городов: {len(cities)}, найдено совпадений: {cities_found}, не найдено: {cities_not_found}")
    return sorted(list(cities))


def filter_by_city(concerts: List[Dict], city: str) -> List[Dict]:
    city_map = {
        'Москва': 'moscow',
        'Санкт-Петербург': 'saint-petersburg',
        'Екатеринбург': 'yekaterinburg',
        'Новосибирск': 'novosibirsk',
        'Казань': 'kazan',
        'Нижний Новгород': 'nizhny-novgorod',
        'Челябинск': 'chelyabinsk',
        'Самара': 'samara',
        'Оренбург': 'orenburg'
    }
    
    city_search_terms = {
        'Москва': ['москва', 'moscow'],
        'Санкт-Петербург': ['санкт-петербург', 'спб', 'питер', 'saint-petersburg', 'st. petersburg', 'st petersburg'],
        'Екатеринбург': ['екатеринбург', 'yekaterinburg'],
        'Новосибирск': ['новосибирск', 'novosibirsk'],
        'Казань': ['казань', 'kazan'],
        'Нижний Новгород': ['нижний новгород', 'nizhny-novgorod'],
        'Челябинск': ['челябинск', 'chelyabinsk'],
        'Самара': ['самара', 'samara'],
        'Оренбург': ['оренбург', 'orenburg']
    }
    
    city_code = city_map.get(city, city.lower())
    search_terms = city_search_terms.get(city, [city.lower()])
    filtered = []
    
    for concert in concerts:
        city_found = False
        
        city_field = concert.get('city', '')
        if city_field and city_field != '-':
            city_field_lower = city_field.lower()
            for term in search_terms:
                if term.lower() in city_field_lower or city_field_lower in term.lower():
                    filtered.append(concert)
                    city_found = True
                    break
        
        if not city_found:
            url = concert.get('url', '')
            if url and f'/{city_code}/' in url:
                filtered.append(concert)
                city_found = True
                continue
        
        if not city_found:
            description = concert.get('description', '')
            if description:
                desc_lower = description.lower()
                for term in search_terms:
                    if term.lower() in desc_lower:
                        filtered.append(concert)
                        city_found = True
                        break
        
        if not city_found:
            venue = concert.get('venue', '')
            if venue:
                venue_lower = venue.lower()
                for term in search_terms:
                    if term.lower() in venue_lower:
                        filtered.append(concert)
                        city_found = True
                        break
        
        if not city_found:
            title = concert.get('title', '')
            if title:
                title_lower = title.lower()
                for term in search_terms:
                    if term.lower() in title_lower:
                        filtered.append(concert)
                        break
    
    filtered = remove_duplicate_concerts(filtered)
    
    logger.info(f"Фильтрация по городу {city}: было {len(concerts)} концертов, стало {len(filtered)} уникальных")
    return filtered


def group_by_artist(concerts: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = {}
    
    for concert in concerts:
        artist = concert.get('matched_artist', 'Неизвестный артист')
        if artist not in grouped:
            grouped[artist] = []
        grouped[artist].append(concert)
    
    return grouped


def extract_date_sort_key(date_str: str) -> tuple:
    if not date_str:
        return (9999, 12, 31)
    
    date_str = date_str.strip()
    
    months_ru = {
        'января': 1, 'янв': 1, 'февраля': 2, 'фев': 2,
        'марта': 3, 'мар': 3, 'апреля': 4, 'апр': 4,
        'мая': 5, 'май': 5, 'июня': 6, 'июн': 6,
        'июля': 7, 'июл': 7, 'августа': 8, 'авг': 8,
        'сентября': 9, 'сен': 9, 'октября': 10, 'окт': 10,
        'ноября': 11, 'ноя': 11, 'декабря': 12, 'дек': 12
    }
    
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if date_match:
        return (int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
    
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
    if date_match:
        return (int(date_match.group(3)), int(date_match.group(2)), int(date_match.group(1)))
    
    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if date_match:
        return (int(date_match.group(3)), int(date_match.group(2)), int(date_match.group(1)))
    
    date_match = re.search(r'(\d{1,2})\s+([а-яё]+)\s+(\d{4})', date_str.lower())
    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2)
        year = int(date_match.group(3))
        month = months_ru.get(month_name, 1)
        return (year, month, day)
    
    date_match = re.search(r'(\d{1,2})\s+([а-яё]+)', date_str.lower())
    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2)
        month = months_ru.get(month_name)
        if month:
            from datetime import datetime
            current_year = datetime.now().year
            return (current_year, month, day)
    
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?!\.\d)', date_str)
    if date_match:
        from datetime import datetime
            current_year = datetime.now().year
            return (current_year, int(date_match.group(2)), int(date_match.group(1)))
    
    logger.debug(f"Не удалось распарсить дату: {date_str[:100]}")
    return (9999, 12, 31)


def format_concert_date_time(concert: Dict) -> str:
    date = get_concert_date(concert) or ''
    time = get_concert_time(concert) or ''
    
    if not date:
        return 'Дата не указана'
    
    months_ru = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        month_name = months_ru.get(month, f'месяца {month}')
        formatted_date = f"{day} {month_name}"
        if time:
            return f"{formatted_date}, {time}"
            return formatted_date
    
    date_clean = re.sub(r',\s*\d{1,2}:\d{2}', '', date)
    date_clean = re.sub(r'\s+в\s+\d{1,2}:\d{2}', '', date_clean)
    date_clean = date_clean.strip()
    
    if time:
        if time in date_clean:
            return date_clean
        return f"{date_clean}, {time}"
    
    return date_clean


def format_concert_message(concerts: list, start_idx: int = 0, limit: int = 10, sort_by: str = 'date') -> str:
    if not concerts:
        return "❌ Концерты не найдены"
    
    concerts = [c for c in concerts if c is not None and isinstance(c, dict)]
    concerts = remove_duplicate_concerts(concerts)
    
    if not concerts:
        return "❌ Концерты не найдены"
    message_parts = []
    total_concerts = len(concerts)
    end_idx = min(start_idx + limit, total_concerts)
    displayed = concerts[start_idx:end_idx]
    
    city_codes = {
        'moscow': 'Москва',
        'saint-petersburg': 'Санкт-Петербург',
        'yekaterinburg': 'Екатеринбург',
        'novosibirsk': 'Новосибирск',
        'kazan': 'Казань',
        'nizhny-novgorod': 'Нижний Новгород',
        'chelyabinsk': 'Челябинск',
        'samara': 'Самара',
        'orenburg': 'Оренбург'
    }
    
    if sort_by == 'artist':
        current_artist = None
        
        for concert in displayed:
            artist = concert.get('matched_artist', 'Неизвестный артист')
            title = concert.get('title', 'Без названия')
            date_time = format_concert_date_time(concert)
            venue = get_concert_venue(concert) or 'Площадка не указана'
            price = concert.get('price', '')
            url = concert.get('url', '')
            
            if artist != current_artist:
                if current_artist is not None:
                    message_parts.append("")  # Пустая строка между артистами
                message_parts.append(f"👤 {artist}")
                current_artist = artist
            
            msg = f"      📅 {date_time}\n"
            msg += f"      📍 {venue}\n"
            if price:
                msg += f"      💰 {price}\n"
            if url:
                city_match = re.search(r'/(moscow|saint-petersburg|yekaterinburg|novosibirsk|kazan|nizhny-novgorod|chelyabinsk|samara|orenburg)/', url)
                if city_match:
                    city_name = city_codes.get(city_match.group(1), city_match.group(1))
                    msg += f"      🌍 {city_name}\n"
            
            message_parts.append(msg)
    else:
        for i, concert in enumerate(displayed, start=start_idx + 1):
            title = concert.get('title', 'Без названия')
            date_time = format_concert_date_time(concert)
            venue = get_concert_venue(concert) or 'Площадка не указана'
            price = concert.get('price', '')
            artist = concert.get('matched_artist', '')
            url = concert.get('url', '')
            
            msg = f"🎵 {i}. {title}\n"
            msg += f"   📅 {date_time}\n"
            msg += f"   📍 {venue}\n"
            if price:
                msg += f"   💰 {price}\n"
            if url:
                city_match = re.search(r'/(moscow|saint-petersburg|yekaterinburg|novosibirsk|kazan|nizhny-novgorod|chelyabinsk|samara|orenburg)/', url)
                if city_match:
                    city_name = city_codes.get(city_match.group(1), city_match.group(1))
                    msg += f"   🌍 {city_name}\n"
            
            message_parts.append(msg)
    
    header = f"🎸 Найдено концертов: {total_concerts}\n"
    
    header += f"Показано {start_idx + 1}-{end_idx} из {total_concerts}\n"
    header += "\n"
    
    return header + "\n".join(message_parts)


def create_city_selection_keyboard(available_cities: list) -> InlineKeyboardMarkup:
    buttons = []
    
    for i in range(0, len(available_cities), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=f"📍 {available_cities[i]}", 
            callback_data=f"city_{available_cities[i]}"
        ))
        if i + 1 < len(available_cities):
            row.append(InlineKeyboardButton(
                text=f"📍 {available_cities[i + 1]}", 
                callback_data=f"city_{available_cities[i + 1]}"
            ))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(
        text="🌍 Все города",
        callback_data="city_all"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_concert_keyboard(concerts: list, current_page: int = 0, page_size: int = 10, 
                           city_filter: str = None, sort_by: str = 'date', available_cities: list = None) -> InlineKeyboardMarkup:
    buttons = []
    
    filter_row = []
    if city_filter:
        filter_row.append(InlineKeyboardButton(text=f"📍 {city_filter}", callback_data="city_change"))
        filter_row.append(InlineKeyboardButton(text="🌍 Все города", callback_data="city_all"))
    elif available_cities and len(available_cities) > 1:
        filter_row.append(InlineKeyboardButton(text="📍 Выбрать город", callback_data="city_select"))
    if filter_row:
        buttons.append(filter_row)
    
    sort_row = []
    if sort_by != 'artist':
        sort_row.append(InlineKeyboardButton(text="👤 По артисту", callback_data="sort_artist"))
    if sort_by != 'date':
        sort_row.append(InlineKeyboardButton(text="📅 По дате", callback_data="sort_date"))
    if sort_row:
        buttons.append(sort_row)
    
    nav_row = []
    total_pages = (len(concerts) + page_size - 1) // page_size
    
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"page_{current_page - 1}"))
    
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"page_{current_page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton(text="✨ Рекомендовано вам", callback_data="recommendations")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

