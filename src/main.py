import sys
import time
import logging
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
src_path = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.services.music_playlist_client import MusicClient
from src.services.playlist_service import ServicePlaylist
from src.services.concert_service import ConcertMatcherService
from src.services.recommendation_service import RecommendationService
from src.utils.url_parser import extract_from_url
from src.utils.concert_utils import get_concert_date, get_concert_time, get_concert_venue
from src.repositories.concert_repository import ConcertRepository
from src.clients.global_concert_client import (
    get_artist_events, 
    convert_ticketmaster_to_afisha_format, 
    TicketmasterError,
    DEFAULT_USER_ARTISTS_LIMIT
)
from src.config.settings import config
from dotenv import load_dotenv
import json
import time

load_dotenv()


def main():
    url = input()
    
    print("Введи город:")
    city_input = input().strip()
    city = city_input if city_input else 'orenburg'

    owner, kind = extract_from_url(url)

    client = MusicClient.from_env()
    playlist_service = ServicePlaylist(client)

    print("Fetching artists from playlist...")
    artist_names = playlist_service.get_artist_names(kind, owner)
    print(f"Found {len(artist_names)} artists in playlist")

    print("\nSearching for concerts...")
    repository = ConcertRepository()
    concert_matcher = ConcertMatcherService(repository, city=city)
    recommendation_service = RecommendationService(repository, city=city)

    # Find concerts from Yandex Afisha
    matching_concerts = concert_matcher.get_all_matching_concerts(artist_names)
    
    # Find concerts from Ticketmaster
    ticketmaster_concerts = {}
    print("\nSearching Ticketmaster for concerts...")
    try:
        artists_to_check = artist_names[:DEFAULT_USER_ARTISTS_LIMIT]
        print(f"Checking first {len(artists_to_check)} artists from playlist...")
        for i, artist_name in enumerate(artists_to_check, 1):
            try:
                print(f"  [{i}/{len(artists_to_check)}] Checking {artist_name}...", end=" ", flush=True)
                events = get_artist_events(artist_name, page_size=10)
                if events:
                    ticketmaster_concerts[artist_name] = events
                    print(f"✓ Found {len(events)} events")
                else:
                    print("✗ No events")
                time.sleep(1.1)  # Rate limiting
            except TicketmasterError as e:
                print(f"✗ Error: {e}")
                continue
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
                continue
    except Exception as e:
        print(f"Error searching Ticketmaster: {e}")

    # Collect all concerts into a single list for pagination
    all_concerts = []
    
    # Add Yandex Afisha concerts
    if matching_concerts:
        artist_to_concerts = concert_matcher.find_concerts_for_artists(artist_names)
        for artist_name, concerts in artist_to_concerts.items():
            for concert in concerts:
                concert['artist_name'] = artist_name
                concert['source'] = 'yandex_afisha'
                all_concerts.append(concert)
    
    # Add Ticketmaster concerts
    if ticketmaster_concerts:
        for artist_name, events in ticketmaster_concerts.items():
            for event in events:
                # Convert Ticketmaster event to concert format
                afisha_event = convert_ticketmaster_to_afisha_format(event)
                afisha_event['artist_name'] = artist_name
                afisha_event['source'] = 'ticketmaster'
                # Add original Ticketmaster data for display
                afisha_event['tm_data'] = event
                all_concerts.append(afisha_event)
    
    # Output summary
    total_concerts = len(all_concerts)
    print(f"\n{'=' * 60}")
    print(f"Найдено концертов: {total_concerts}")
    if matching_concerts:
        print(f"  - Yandex Afisha: {len(matching_concerts)}")
    if ticketmaster_concerts:
        total_tm_events = sum(len(events) for events in ticketmaster_concerts.values())
        print(f"  - Ticketmaster: {total_tm_events}")
    print(f"Город: {city}")
    print(f"{'=' * 60}\n")
    
    # Display concerts with pagination (10 per page)
    if all_concerts:
        page_size = 10
        total_pages = (total_concerts + page_size - 1) // page_size
        current_page = 0
        
        while current_page < total_pages:
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, total_concerts)
            page_concerts = all_concerts[start_idx:end_idx]
            
            print(f"\n{'=' * 60}")
            print(f"Показано {start_idx + 1}-{end_idx} из {total_concerts}")
            print(f"Страница {current_page + 1} из {total_pages}")
            print(f"{'=' * 60}\n")
            
            for i, concert in enumerate(page_concerts, start=start_idx + 1):
                artist_name = concert.get('artist_name', 'Unknown')
                source = concert.get('source', '')
                title = concert.get('title', 'N/A')
                url = concert.get('url', '')
                
                # Display based on source
                if source == 'ticketmaster':
                    tm_data = concert.get('tm_data', {})
                    event_datetime = tm_data.get('datetime', '')
                    event_venue = tm_data.get('venue', '')
                    event_city = tm_data.get('city', '')
                    event_country = tm_data.get('country', '')
                    
                    print(f"{i}. 🎵 {artist_name} (Ticketmaster)")
                    print(f"   📅 {title}")
                    if event_datetime:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(event_datetime.replace('Z', '+00:00'))
                            print(f"   Дата: {dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            print(f"   Дата: {event_datetime}")
                    if event_venue:
                        location = f"{event_venue}"
                        if event_city:
                            location += f", {event_city}"
                        if event_country:
                            location += f", {event_country}"
                        print(f"   Место: {location}")
                    if url:
                        print(f"   URL: {url}")
                else:
                    date = get_concert_date(concert)
                    concert_time = get_concert_time(concert)
                    venue = get_concert_venue(concert)
                    price = concert.get('price', '')
                    
                    print(f"{i}. 🎵 {artist_name}")
                    print(f"   📅 {title}")
                    if date:
                        print(f"   Дата: {date}")
                    if concert_time:
                        print(f"   Время: {concert_time}")
                    if venue:
                        print(f"   Место: {venue}")
                    if price:
                        print(f"   Цена: {price}")
                    if url:
                        print(f"   URL: {url}")
                print()
            
            # Ask for next page
            if current_page < total_pages - 1:
                print(f"{'=' * 60}")
                user_input = input(f"Нажмите Enter для следующей страницы (или 'q' для выхода): ").strip().lower()
                if user_input == 'q':
                    break
                current_page += 1
            else:
                print(f"{'=' * 60}")
                print("Все концерты показаны.")
                break
    else:
        print("Концерты не найдены.")
        print("\nАртисты из плейлиста:")
        for name in artist_names[:20]:
            print(f"  - {name}")
        if len(artist_names) > 20:
            print(f"  ... и ещё {len(artist_names) - 20}")

    # Get AI recommendations - separate message
    print(f"\n\n{'=' * 60}")
    print("=" * 60)
    print("РЕКОМЕНДОВАНО ВАМ")
    print("=" * 60)
    print("=" * 60)
    
    if recommendation_service.enabled:
        print("\nАнализирую музыкальные стили и ищу похожие концерты...")
        recommended_concerts = recommendation_service.get_recommendations(
            artist_names, 
            max_recommendations=10
        )
        
        if recommended_concerts:
            print(f"\n✨ Найдено {len(recommended_concerts)} рекомендованных концертов:\n")
            for i, concert in enumerate(recommended_concerts, 1):
                title = concert.get('title', 'N/A')
                url = concert.get('url', '')
                
                date = get_concert_date(concert)
                concert_time = get_concert_time(concert)
                venue = get_concert_venue(concert)
                price = concert.get('price', '')
                
                print(f"{i}. 🎭 {title}")
                if date:
                    print(f"   Дата: {date}")
                if concert_time:
                    print(f"   Время: {concert_time}")
                if venue:
                    print(f"   Место: {venue}")
                if price:
                    print(f"   Цена: {price}")
                if url:
                    print(f"   URL: {url}")
                print()
        else:
            print("\n⚠️  Рекомендации не найдены.")
            print("   Возможные причины:")
            print("   - Квота API исчерпана (проверьте: https://ai.dev/usage?tab=rate-limit)")
            print("   - Не найдено подходящих концертов по музыкальному стилю")
            print("   - Ошибка API (проверьте логи выше)")
    else:
        print("\nРекомендации отключены. Установите GEMINI_API_KEY для включения.")
    
    print(f"\n{'=' * 60}")

    repository.close()


if __name__ == "__main__":
    main()