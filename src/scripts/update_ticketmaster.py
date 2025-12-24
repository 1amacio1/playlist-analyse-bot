import asyncio
import sys
from pathlib import Path
from typing import List
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
import csv

project_root = Path(__file__).parent.parent.parent
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.clients.global_concert_client import get_artist_events, convert_ticketmaster_to_afisha_format
from src.repositories.concert_repository import ConcertRepository
from src.db.database import async_session_maker, close_db
from src.config.settings import config

MAX_CONCURRENT = 1
ARTISTS_CSV = src_path / "artists.csv"
ARTISTS_LIMIT = 100

def load_artists_from_csv(limit: int = 100) -> List[str]:
    artists = []

    if not ARTISTS_CSV.exists():
        print(f"Error: File {ARTISTS_CSV} not found", file=sys.stderr)
        return artists

    try:
        with open(ARTISTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    artist_name = row[0].strip()
                    artists.append(artist_name)
                    if len(artists) >= limit:
                        break
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)

    return artists

async def fetch_event(semaphore, artist):
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            events = await loop.run_in_executor(None, get_artist_events, artist)
            await asyncio.sleep(1.1)
            return artist, events
        except Exception as e:
            print(f"Error fetching {artist}: {e}", file=sys.stderr)
            return artist, []

async def main():
    try:
        print(f"Connecting to PostgreSQL at {config.DB_HOST}:{config.DB_PORT}...")
        async with async_session_maker() as session:
            await session.execute(select(1))
        print("✓ Successfully connected to PostgreSQL")
    except OperationalError as e:
        print("\n" + "="*60, file=sys.stderr)
        print("ERROR: Failed to connect to PostgreSQL", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\nConnection details:", file=sys.stderr)
        print(f"  Host: {config.DB_HOST}", file=sys.stderr)
        print(f"  Port: {config.DB_PORT}", file=sys.stderr)
        print(f"  Database: {config.DB_NAME}", file=sys.stderr)
        print(f"  Username: {config.DB_USERNAME}", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        print("\nPlease ensure PostgreSQL is running:", file=sys.stderr)
        print("  • If using Docker: docker-compose up -d postgres", file=sys.stderr)
        print("  • If installed locally: pg_ctl start (or brew services start postgresql)", file=sys.stderr)
        print("  • Or check your .env file for DB_* variables", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        return
    except Exception as e:
        print(f"\nUnexpected error connecting to PostgreSQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return

    repository = ConcertRepository()

    try:
        print(f"Loading artists from {ARTISTS_CSV}...")
        artists = load_artists_from_csv(limit=ARTISTS_LIMIT)

        if not artists:
            print(f"Error: No artists found in {ARTISTS_CSV}")
            print("Please ensure the file exists and contains artist names (one per line)")
            return

        print(f"✓ Loaded {len(artists)} artists from CSV")
        print(f"Processing {len(artists)} artists...")

        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        tasks = [fetch_event(semaphore, artist) for artist in artists]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_events = 0
        processed_count = 0
        events_to_save = []

        for result in results:
            if isinstance(result, Exception):
                print(f"Task failed with exception: {result}", file=sys.stderr)
                continue

            artist_name, events = result

            if not events:
                continue

            for e in events:
                try:
                    doc = convert_ticketmaster_to_afisha_format(e)
                    doc["artist_name"] = artist_name
                    events_to_save.append(doc)
                except Exception as e:
                    print(f"Error converting event: {e}", file=sys.stderr)
                    continue

            total_events += len(events)
            processed_count += 1
            print(f"{artist_name}: {len(events)} events found")

        saved_count = 0
        if events_to_save:
            print(f"\nSaving {len(events_to_save)} events to database...")
            saved_count = await repository.save_events_batch(events_to_save)
            print(f"✓ Saved {saved_count} new events")
            print(f"  (Skipped {len(events_to_save) - saved_count} duplicates)")
        else:
            print("\nNo events to save")

        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Artists processed: {processed_count}")
        print(f"  Total events found: {total_events}")
        print(f"  Events saved: {saved_count}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        try:
            await repository.close()
            await close_db()
            print("\nDatabase connections closed")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())

