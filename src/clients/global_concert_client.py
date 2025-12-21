# src/clients/global_concert_client.py
import os
import sys
import time
import random
import requests
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from pymongo import MongoClient

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.repositories.concert_repository import ConcertRepository
from src.config.settings import config

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("TICKETMASTER_API_TOKEN")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# MongoDB settings for artists
ARTISTS_DB = "artists_db"
ARTISTS_COLLECTION = "big_artists"

DEFAULT_INTERVAL_HOURS = 6
DEFAULT_SCHEDULED_ARTISTS_LIMIT = 100
DEFAULT_USER_ARTISTS_LIMIT = 20

class TicketmasterError(Exception):
    pass

def get_artist_events(
    artist: str,
    api_token: str | None = None,
    retries: int = 3,
    page_size: int = 20
):
    token = api_token or API_TOKEN
    if not token:
        raise TicketmasterError("TICKETMASTER_API_TOKEN is not set")

    params = {
        "apikey": token,
        "keyword": artist,
        "size": page_size
    }

    headers = {"User-Agent": "Mozilla/5.0 (Ticketmaster Collector Bot)"}

    for attempt in range(retries):
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            events = data.get("_embedded", {}).get("events", [])
            result = []

            for e in events:
                venue = e.get("_embedded", {}).get("venues", [{}])[0]
                result.append({
                    "artist_name": artist,
                    "event_name": e.get("name"),
                    "datetime": e.get("dates", {}).get("start", {}).get("dateTime"),
                    "venue": venue.get("name"),
                    "city": venue.get("city", {}).get("name"),
                    "country": venue.get("country", {}).get("name"),
                    "fetched_at": datetime.utcnow(),
                    "timezone": e.get("dates", {}).get("timezone"),
                    "url": e.get("_links", {}).get("self", {}).get("href"),
                    "source": "ticketmaster"
                })
            return result

        if response.status_code == 429:
            sleep_time = (2 ** attempt) + random.uniform(0.2, 0.6)
            logger.warning(f"[Ticketmaster] 429 for '{artist}', retry in {sleep_time:.1f}s (attempt {attempt+1}/{retries})")
            time.sleep(sleep_time)
            continue

        raise TicketmasterError(f"Ticketmaster API error {response.status_code}: {response.text}")

    return []


def get_artists_from_db() -> List[str]:
    """Get list of artists from MongoDB"""
    try:
        client = MongoClient(config.mongo_uri)
        db = client[ARTISTS_DB]
        collection = db[ARTISTS_COLLECTION]
        artists = list(collection.find({}, {"artist_name": 1, "_id": 0}))
        client.close()
        return [artist["artist_name"] for artist in artists]
    except Exception as e:
        logger.error(f"Error getting artists from DB: {e}")
        return []


def convert_ticketmaster_to_afisha_format(event: Dict) -> Dict:
    """Convert Ticketmaster event format to Afisha DB format"""
    return {
        "title": event.get("event_name", "-"),
        "url": event.get("url", "-"),
        "category": "concert",
        "description": f"{event.get('city', '-')}, {event.get('venue', '-')}",
        "date": event.get("datetime", "-"),
        "price": "-",
        "venue": event.get("venue", "-"),
        "image": "-",
        "full_title": event.get("event_name", "-"),
        "source": "ticketmaster"
    }


def process_artists(artists: List[str], limit: int = None) -> tuple:
    """Process artists and save events to database"""
    if not API_TOKEN:
        logger.error("TICKETMASTER_API_TOKEN is not set")
        return 0, 0
    
    db = ConcertRepository()
    artists_to_process = artists[:limit] if limit else artists
    total_events = 0
    total_saved = 0
    
    logger.info(f"Processing {len(artists_to_process)} artists...")
    
    for i, artist in enumerate(artists_to_process, 1):
        try:
            logger.info(f"[{i}/{len(artists_to_process)}] Fetching events for: {artist}")
            events = get_artist_events(artist)
            
            if events:
                saved_count = 0
                for event in events:
                    afisha_event = convert_ticketmaster_to_afisha_format(event)
                    if db.save_event(afisha_event):
                        saved_count += 1
                
                total_events += len(events)
                total_saved += saved_count
                logger.info(f"  Found {len(events)} events, saved {saved_count} new")
            else:
                logger.info(f"  No events found")
            
            # Rate limiting - wait between requests
            if i < len(artists_to_process):
                time.sleep(1.1)
                
        except Exception as e:
            logger.error(f"Error processing {artist}: {e}")
            continue
    
    db.close()
    return total_events, total_saved


def run_ticketmaster_update(limit: int = None):
    """Run single update of Ticketmaster events"""
    logger.info("=" * 60)
    logger.info("Ticketmaster Event Updater")
    logger.info("=" * 60)
    
    artists = get_artists_from_db()
    if not artists:
        logger.warning("No artists found in database. Run load_artists.py first.")
        return
    
    logger.info(f"Found {len(artists)} artists in database")
    
    initial_count = ConcertRepository().count_events_by_category('concert')
    ConcertRepository().close()
    logger.info(f"Current concerts in database: {initial_count}")
    
    total_events, total_saved = process_artists(artists, limit=limit)
    
    final_count = ConcertRepository().count_events_by_category('concert')
    ConcertRepository().close()
    
    logger.info("\n" + "=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Artists processed: {len(artists[:limit]) if limit else len(artists)}")
    logger.info(f"Total events found: {total_events}")
    logger.info(f"New events saved: {total_saved}")
    logger.info(f"Duplicates skipped: {total_events - total_saved}")
    logger.info(f"Initial concerts in database: {initial_count}")
    logger.info(f"Final concerts in database: {final_count}")
    logger.info(f"New concerts added: {final_count - initial_count}")
    logger.info("=" * 60)


def run_scheduled_updates(interval_seconds: int, artists_limit: int = DEFAULT_SCHEDULED_ARTISTS_LIMIT):
    """Run Ticketmaster updates periodically with specified interval"""
    logger.info("=" * 60)
    logger.info("Starting scheduled Ticketmaster updates")
    logger.info(f"Interval: {interval_seconds / 3600:.1f} hours ({interval_seconds} seconds)")
    logger.info(f"Artists per run: {artists_limit}")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            logger.info("\n" + "=" * 60)
            logger.info(f"SCHEDULED RUN #{iteration}")
            logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Processing {artists_limit} artists")
            logger.info("=" * 60)
            
            try:
                run_ticketmaster_update(limit=artists_limit)
                logger.info(f"\n✓ Run #{iteration} completed successfully")
            except KeyboardInterrupt:
                logger.info("\nScheduled updates stopped by user")
                break
            except Exception as e:
                logger.error(f"\n✗ Run #{iteration} failed: {e}", exc_info=True)
                logger.info("Continuing with next scheduled run...")
            
            # Calculate next run time
            next_run = datetime.fromtimestamp(time.time() + interval_seconds)
            logger.info("\n" + "=" * 60)
            logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Waiting {interval_seconds / 3600:.1f} hours...")
            logger.info("=" * 60)
            
            # Wait for next iteration
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scheduled updates stopped by user")
        logger.info("=" * 60)


def main():
    """Main function with CLI arguments"""
    parser = argparse.ArgumentParser(
        description='Update concerts from Ticketmaster API',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run updates periodically (default: every 6 hours)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_INTERVAL_HOURS,
        help=f'Interval between runs in hours (default: {DEFAULT_INTERVAL_HOURS})'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help=f'Limit number of artists to process (default: {DEFAULT_USER_ARTISTS_LIMIT} for single run, {DEFAULT_SCHEDULED_ARTISTS_LIMIT} for scheduled)'
    )
    
    args = parser.parse_args()
    
    # Scheduled mode
    if args.schedule:
        interval_seconds = args.interval * 3600
        artists_limit = args.limit if args.limit else DEFAULT_SCHEDULED_ARTISTS_LIMIT
        run_scheduled_updates(interval_seconds, artists_limit=artists_limit)
        return
    
    # Single run mode
    artists_limit = args.limit if args.limit else DEFAULT_USER_ARTISTS_LIMIT
    run_ticketmaster_update(limit=artists_limit)


if __name__ == '__main__':
    main()