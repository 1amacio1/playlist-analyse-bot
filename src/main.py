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
from src.utils.url_parser import extract_from_url
from src.utils.concert_utils import get_concert_date, get_concert_time, get_concert_venue
from src.repositories.concert_repository import ConcertRepository
from src.config.settings import config
from dotenv import load_dotenv
import json

load_dotenv()


def main():
    url = input()
    
    print("Введи городо")
    city_input = input().strip()
    city = city_input if city_input else config.CITY

    owner, kind = extract_from_url(url)

    client = MusicClient.from_env()
    playlist_service = ServicePlaylist(client)

    print("Fetching artists from playlist...")
    artist_names = playlist_service.get_artist_names(kind, owner)
    print(f"Found {len(artist_names)} artists in playlist")

    print("\nSearching for concerts...")
    repository = ConcertRepository()
    concert_matcher = ConcertMatcherService(repository, city=city)

    # Find concerts matching artists
    matching_concerts = concert_matcher.get_all_matching_concerts(artist_names)

    # Output results
    print(f"\n{'=' * 60}")
    print(f"Found {len(matching_concerts)} concerts matching artists from playlist")
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
        print("No concerts found matching artists from playlist.")
        print("\nArtists from playlist:")
        for name in artist_names:
            print(f"  - {name}")

    repository.close()


if __name__ == "__main__":
    main()