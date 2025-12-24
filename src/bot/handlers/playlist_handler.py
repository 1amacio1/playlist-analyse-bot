import re
import logging
from typing import Dict, List
from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.services.music_playlist_client import MusicClient
from src.services.playlist_service import ServicePlaylist
from src.repositories.concert_repository import ConcertRepository
from src.utils.url_parser import extract_from_url
from src.utils.concert_utils import get_concert_date
from src.clients.global_concert_client import (
    get_artist_events,
    convert_ticketmaster_to_afisha_format,
    TicketmasterError,
    DEFAULT_USER_ARTISTS_LIMIT
)
import asyncio

from src.bot.utils import (
    remove_duplicate_concerts,
    get_available_cities,
    filter_by_city,
    group_by_artist,
    extract_date_sort_key,
    format_concert_message,
    create_city_selection_keyboard,
    create_concert_keyboard
)

logger = logging.getLogger(__name__)

class ConcertService:
    def __init__(self, repository: ConcertRepository):
        from src.services.concert_service import ConcertMatcherService
        self.matcher = ConcertMatcherService(repository, city='')
        self.repository = repository

    def get_available_cities(self, concerts: list) -> list:
        return get_available_cities(concerts)

    def find_concerts_by_artists(self, artist_names: list) -> list:
        all_concerts = self.repository.get_events_by_category('concert')
        logger.info(f"Found {len(all_concerts)} concerts in database (all cities and sources)")

        source_counts_db = {}
        city_counts_db = {}
        for concert in all_concerts[:200]:
            source = concert.get('source', 'unknown')
            source_counts_db[source] = source_counts_db.get(source, 0) + 1

            url = concert.get('url', '')
            city_field = concert.get('city', '')
            if url:
                city_match = re.search(r'/(moscow|saint-petersburg|yekaterinburg|novosibirsk|kazan|nizhny-novgorod|chelyabinsk|samara|orenburg)/', url)
                if city_match:
                    city_code = city_match.group(1)
                    city_counts_db[city_code] = city_counts_db.get(city_code, 0) + 1
            elif city_field and city_field != '-':
                city_counts_db[city_field] = city_counts_db.get(city_field, 0) + 1

        logger.info(f"Sample distribution by source in DB: {source_counts_db}")
        logger.info(f"Sample distribution by city in DB: {city_counts_db}")

        artist_to_concerts = {}
        for artist_name in artist_names:
            matching_concerts = []
            for concert in all_concerts:
                title = concert.get('title', '')
                if title and self.matcher.find_artist_in_text(artist_name, title):
                    matching_concerts.append(concert)
                    continue

                full_title = concert.get('full_title', '')
                if full_title and self.matcher.find_artist_in_text(artist_name, full_title):
                    matching_concerts.append(concert)
                    continue

                description = concert.get('description', '')
                if description and len(description) > 20:
                    normalized_artist = self.matcher.normalize_name(artist_name)
                    artist_clean = re.sub(r'[^\w\s]', '', normalized_artist)
                    desc_clean = re.sub(r'[^\w\s]', '', description.lower())

                    if len(artist_clean) >= 4:
                        pattern = r'\b' + re.escape(artist_clean) + r'\b'
                        if re.search(pattern, desc_clean):
                            matching_concerts.append(concert)
                            continue

            if matching_concerts:
                artist_to_concerts[artist_name] = matching_concerts
        seen_urls = set()
        url_to_artists = {}
        concerts = []

        for artist_name, artist_concerts in artist_to_concerts.items():
            for concert in artist_concerts:
                url = concert.get('url')
                if url:
                    if url not in url_to_artists:
                        url_to_artists[url] = []
                    url_to_artists[url].append(artist_name)

        for artist_concerts in artist_to_concerts.values():
            for concert in artist_concerts:
                url = concert.get('url')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    if url in url_to_artists:
                        concert['matched_artist'] = ', '.join(url_to_artists[url])
                    concerts.append(concert)

        logger.info(f"Found {len(concerts)} unique concerts matching artists (all cities)")

        unique_concerts = remove_duplicate_concerts(concerts)
        city_counts = {}
        source_counts = {}
        for concert in unique_concerts:
            source = concert.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
            url = concert.get('url', '')
            description = concert.get('description', '')
            venue = concert.get('venue', '')

            city_found = False
            if url:
                city_match = re.search(r'/(moscow|saint-petersburg|yekaterinburg|novosibirsk|kazan|nizhny-novgorod|chelyabinsk|samara|orenburg)/', url)
                if city_match:
                    city_code = city_match.group(1)
                    city_counts[city_code] = city_counts.get(city_code, 0) + 1
                    city_found = True

            if not city_found:
                city_field = concert.get('city', '')
                if city_field and city_field != '-':
                    city_field_lower = city_field.lower()
                    city_mapping = {
                        'москва': 'moscow',
                        'moscow': 'moscow',
                        'санкт-петербург': 'saint-petersburg',
                        'saint petersburg': 'saint-petersburg',
                        'st. petersburg': 'saint-petersburg',
                        'st petersburg': 'saint-petersburg',
                        'спб': 'saint-petersburg',
                        'питер': 'saint-petersburg',
                        'екатеринбург': 'yekaterinburg',
                        'yekaterinburg': 'yekaterinburg',
                        'новосибирск': 'novosibirsk',
                        'novosibirsk': 'novosibirsk',
                        'казань': 'kazan',
                        'kazan': 'kazan',
                        'нижний новгород': 'nizhny-novgorod',
                        'nizhny novgorod': 'nizhny-novgorod',
                        'челябинск': 'chelyabinsk',
                        'chelyabinsk': 'chelyabinsk',
                        'самара': 'samara',
                        'samara': 'samara',
                        'оренбург': 'orenburg',
                        'orenburg': 'orenburg'
                    }
                    for city_name, city_code in city_mapping.items():
                        if city_name in city_field_lower or city_field_lower in city_name:
                            city_counts[city_code] = city_counts.get(city_code, 0) + 1
                            city_found = True
                            break

            if not city_found:
                text_to_check = f"{description} {venue}".lower()
                city_mapping = {
                    'москва': 'moscow',
                    'санкт-петербург': 'saint-petersburg',
                    'спб': 'saint-petersburg',
                    'питер': 'saint-petersburg',
                    'екатеринбург': 'yekaterinburg',
                    'новосибирск': 'novosibirsk',
                    'казань': 'kazan',
                    'нижний новгород': 'nizhny-novgorod',
                    'челябинск': 'chelyabinsk',
                    'самара': 'samara',
                    'оренбург': 'orenburg'
                }
                for city_name, city_code in city_mapping.items():
                    if city_name in text_to_check:
                        city_counts[city_code] = city_counts.get(city_code, 0) + 1
                        break

        logger.info(f"Дедупликация: было {len(concerts)} концертов, стало {len(unique_concerts)} уникальных")
        logger.info(f"Распределение по городам: {city_counts}")
        logger.info(f"Распределение по источникам: {source_counts}")
        return unique_concerts

    def filter_by_city(self, concerts: list, city: str) -> list:
        return filter_by_city(concerts, city)

    def group_by_artist(self, concerts: list) -> dict:
        return group_by_artist(concerts)

async def handle_playlist_url(message: Message, state: FSMContext, user_results: Dict):
    user_id = message.from_user.id

    try:
        url = message.text or ""
        url = url.strip()

        try:
            owner, kind = extract_from_url(url)
            logger.info(f"Извлечено из URL: owner={owner}, kind={kind}")
        except ValueError as e:
            logger.error(f"Ошибка извлечения URL: {e}, текст: {url[:200]}")
            if 'music.yandex' not in url.lower() and 'playlist' not in url.lower():
                await message.answer(
                    "❌ Неверный формат. Пожалуйста, отправьте ссылку на публичный плейлист Яндекс Музыки "
                    "или HTML-код с iframe плейлиста.\n\n"
                    "Используйте /help для получения инструкций."
                )
                return
            else:
                await message.answer(
                    f"❌ Не удалось извлечь ссылку на плейлист.\n\n"
                    f"Ошибка: {str(e)}\n\n"
                    f"Пожалуйста, проверьте формат ссылки. Убедитесь, что:\n"
                    f"• Плейлист публичный\n"
                    f"• Ссылка содержит /iframe/playlist/ или /users/.../playlists/\n"
                    f"• Используйте /help для примеров"
                )
                return

        status_msg = await message.answer("⏳ Сканирую плейлист (это займет ~2-3 минуты)...")

        try:
            music_client = MusicClient.from_env()
            playlist_service = ServicePlaylist(music_client)
            repository = ConcertRepository()
            concert_service = ConcertService(repository)
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            await status_msg.edit_text("❌ Ошибка инициализации сервисов. Проверьте настройки.")
            await state.clear()
            return

        try:
            playlist = music_client.get_playlist(kind, owner)
            tracks = playlist.fetch_tracks()

            total_tracks = 0
            tracks_list = []
            for tr in tracks:
                tracks_list.append(tr)
                total_tracks += 1

            artists = set()
            processed = 0

            for tr in tracks_list:
                t = tr.track
                if t and t.artists:
                    for artist in t.artists:
                        if artist.name:
                            artists.add(artist.name)
                processed += 1

                if processed % 50 == 0:
                    try:
                        await status_msg.edit_text(
                            f"⏳ Обработано {processed}/{total_tracks if total_tracks > 0 else '?'} треков..."
                        )
                    except:
                        pass

            artist_list = list(artists)

            await status_msg.edit_text(
                f"✅ Найдено {len(artist_list)} уникальных артистов\n"
                f"🔍 Ищу концерты в базе данных..."
            )

            concerts = concert_service.find_concerts_by_artists(artist_list)
            logger.info(f"Найдено концертов в БД: {len(concerts)}")

            ticketmaster_concerts = []
            try:
                await status_msg.edit_text(
                    f"✅ Найдено {len(concerts)} концертов в БД\n"
                    f"🌍 Ищу концерты через Ticketmaster..."
                )

                artists_to_check = artist_list[:20]
                logger.info(f"Проверяю {len(artists_to_check)} артистов из плейлиста пользователя через Ticketmaster API")

                for i, artist_name in enumerate(artists_to_check, 1):
                    try:
                        if i % 5 == 0:
                            try:
                                await status_msg.edit_text(
                                    f"✅ Найдено {len(concerts)} концертов в БД\n"
                                    f"🌍 Проверяю Ticketmaster: {i}/{len(artists_to_check)} артистов..."
                                )
                            except:
                                pass

                        events = get_artist_events(artist_name, page_size=10)
                        if events:
                            for event in events:
                                afisha_event = convert_ticketmaster_to_afisha_format(event)
                                afisha_event['matched_artist'] = artist_name
                                ticketmaster_concerts.append(afisha_event)

                            logger.info(f"Найдено {len(events)} концертов для {artist_name} через Ticketmaster")

                        await asyncio.sleep(1.1)
                    except TicketmasterError as e:
                        logger.warning(f"Ошибка Ticketmaster для {artist_name}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка при поиске через Ticketmaster для {artist_name}: {e}")
                        continue

                logger.info(f"Найдено {len(ticketmaster_concerts)} концертов через Ticketmaster API")

            except Exception as e:
                logger.error(f"Ошибка при поиске через Ticketmaster: {e}", exc_info=True)

            all_concerts = concerts + ticketmaster_concerts
            logger.info(f"Всего концертов (БД + Ticketmaster): {len(all_concerts)}")

            unique_concerts = remove_duplicate_concerts(all_concerts)
            logger.info(f"После дедупликации: было {len(all_concerts)} концертов, стало {len(unique_concerts)} уникальных")

            available_cities = get_available_cities(unique_concerts)
            logger.info(f"Найдено городов: {len(available_cities)}, города: {available_cities}")

            sorted_concerts = sorted(unique_concerts,
                                   key=lambda x: extract_date_sort_key(
                                       get_concert_date(x) or ''
                                   ))
            sorted_concerts = remove_duplicate_concerts(sorted_concerts)

            user_results[user_id] = {
                'concerts': sorted_concerts,
                'original_concerts': sorted_concerts.copy(),
                'artists': artist_list,
                'city_filter': None,
                'sort_by': 'date',
                'current_page': 0,
                'concert_service': concert_service,
                'repository': repository,
                'available_cities': available_cities
            }

            if sorted_concerts:
                if len(available_cities) > 0:
                    city_keyboard = create_city_selection_keyboard(available_cities)
                    await status_msg.edit_text(
                        f"✅ Найдено {len(sorted_concerts)} концертов в {len(available_cities)} городе(ах).\n\n"
                        f"📍 Выберите город для просмотра концертов или нажмите '🌍 Все города' для просмотра всех событий:",
                        reply_markup=city_keyboard
                    )
                else:
                    concert_text = format_concert_message(sorted_concerts, 0, 10, 'date')
                    keyboard = create_concert_keyboard(sorted_concerts, 0, 10, None, 'date', available_cities)

                    await status_msg.edit_text(
                        f"✅ Готово! Вот список концертов по вашим интересам:\n\n{concert_text}",
                        reply_markup=keyboard
                    )
            else:
                await status_msg.edit_text(
                    f"😔 К сожалению, концерты для ваших артистов не найдены.\n"
                    f"Найдено артистов: {len(artist_list)}\n\n"
                    f"Возможно, концерты еще не добавлены в базу данных. "
                    f"Попробуйте запустить парсер концертов."
                )

            await state.clear()

        except Exception as e:
            logger.error(f"Ошибка обработки плейлиста: {e}", exc_info=True)
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg.lower():
                user_msg = (
                    f"❌ Плейлист не найден.\n\n"
                    f"Возможные причины:\n"
                    f"• Плейлист не публичный (сделайте его публичным в настройках)\n"
                    f"• Неверная ссылка\n"
                    f"• Плейлист был удален"
                )
            elif "token" in error_msg.lower() or "auth" in error_msg.lower():
                user_msg = (
                    f"❌ Ошибка авторизации.\n\n"
                    f"Проверьте, что токен Яндекс Музыки (YANDEX_MUSIC_TOKEN) "
                    f"в файле .env настроен правильно."
                )
            else:
                user_msg = (
                    f"❌ Произошла ошибка при обработке плейлиста.\n\n"
                    f"Ошибка: {error_msg[:200]}\n\n"
                    f"Проверьте, что:\n"
                    f"• Плейлист публичный\n"
                    f"• Ссылка корректна\n"
                    f"• Токен Яндекс Музыки настроен правильно"
                )
            try:
                await status_msg.edit_text(user_msg)
            except:
                await message.answer(user_msg)
            await state.clear()
        finally:
            try:
                await repository.close()
            except:
                pass

    except Exception as e:
        logger.error(f"Общая ошибка: {e}", exc_info=True)
        await message.answer("❌ Произошла непредвиденная ошибка. Попробуйте позже.")
        await state.clear()

