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

    # Output results
    print(f"\n{'=' * 60}")
    print(f"Found {len(matching_concerts)} concerts from Yandex Afisha matching artists from playlist")
    if ticketmaster_concerts:
        total_tm_events = sum(len(events) for events in ticketmaster_concerts.values())
        print(f"Found {total_tm_events} concerts from Ticketmaster for {len(ticketmaster_concerts)} artists")
    print(f"City: {city}")
    print(f"{'=' * 60}\n")

    if matching_concerts:
        artist_to_concerts = concert_matcher.find_concerts_for_artists(artist_names)

        for artist_name, concerts in artist_to_concerts.items():
            print(f"\n🎵 {artist_name}:")
            for concert in concerts:
                title = concert.get('title', 'N/A')
                url = concert.get('url', '')
                
                date = get_concert_date(concert)
                time = get_concert_time(concert)
                venue = get_concert_venue(concert)
                price = concert.get('price', '')

                print(f"  📅 {title}")
                if date:
                    print(f"     Дата: {date}")
                if time:
                    print(f"     Время: {time}")
                if venue:
                    print(f"     Место: {venue}")
                if price:
                    print(f"     Цена: {price}")
                if url:
                    print(f"     URL: {url}")
                print()
    else:
        print("No concerts found matching artists from playlist in Yandex Afisha.")
    
    # Display Ticketmaster concerts
    if ticketmaster_concerts:
        print(f"\n{'=' * 60}")
        print("Ticketmaster Concerts")
        print(f"{'=' * 60}\n")
        
        for artist_name, events in ticketmaster_concerts.items():
            print(f"\n🎵 {artist_name} (Ticketmaster):")
            for event in events[:5]:  # Show max 5 events per artist
                event_name = event.get('event_name', 'N/A')
                event_url = event.get('url', '')
                event_datetime = event.get('datetime', '')
                event_venue = event.get('venue', '')
                event_city = event.get('city', '')
                event_country = event.get('country', '')
                
                print(f"  📅 {event_name}")
                if event_datetime:
                    # Parse datetime if available
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(event_datetime.replace('Z', '+00:00'))
                        print(f"     Дата: {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        print(f"     Дата: {event_datetime}")
                if event_venue:
                    location = f"{event_venue}"
                    if event_city:
                        location += f", {event_city}"
                    if event_country:
                        location += f", {event_country}"
                    print(f"     Место: {location}")
                if event_url:
                    print(f"     URL: {event_url}")
                print()
    
    if not matching_concerts and not ticketmaster_concerts:
        print("\nArtists from playlist:")
        for name in artist_names[:20]:
            print(f"  - {name}")
        if len(artist_names) > 20:
            print(f"  ... and {len(artist_names) - 20} more")

    # Get AI recommendations based on music style analysis
    print(f"\n{'=' * 60}")
    print("AI Recommendations based on music style analysis...")
    print(f"{'=' * 60}\n")
    
    if recommendation_service.enabled:
        print("Analyzing music styles and finding similar concerts...")
        recommended_concerts = recommendation_service.get_recommendations(
            artist_names, 
            max_recommendations=10
        )
        
        if recommended_concerts:
            print(f"\n✨ Found {len(recommended_concerts)} recommended concerts:")
            for concert in recommended_concerts:
                title = concert.get('title', 'N/A')
                url = concert.get('url', '')
                
                date = get_concert_date(concert)
                time = get_concert_time(concert)
                venue = get_concert_venue(concert)
                price = concert.get('price', '')
                
                print(f"\n  🎭 {title}")
                if date:
                    print(f"     Дата: {date}")
                if time:
                    print(f"     Время: {time}")
                if venue:
                    print(f"     Место: {venue}")
                if price:
                    print(f"     Цена: {price}")
                if url:
                    print(f"     URL: {url}")
        else:
            print("⚠️  No recommendations found.")
            print("   This could be due to:")
            print("   - API quota exceeded (check: https://ai.dev/usage?tab=rate-limit)")
            print("   - No suitable concerts found based on music style")
            print("   - API error (check logs above)")
    else:
        print("AI recommendations disabled. Set GEMINI_API_KEY environment variable to enable.")

    repository.close()


if __name__ == "__main__":
    main()