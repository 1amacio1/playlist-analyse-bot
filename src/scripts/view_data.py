
import sys
import re
import asyncio
from pathlib import Path
from sqlalchemy import select, distinct, func
from sqlalchemy.exc import OperationalError

project_root = Path(__file__).parent.parent.parent
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.repositories.concert_repository import ConcertRepository
from src.db.models import Event
from src.db.database import async_session_maker, close_db
from src.config.settings import config

def print_separator(char="=", length=60):
    print(char * length)

def extract_date_from_description(description):
    if not description:
        return None

    parts = description.split('•')
    if parts and len(parts) > 0:
        date_part = parts[0].strip()
        date_part = re.sub(r',\s*\d{1,2}:\d{2}', '', date_part)
        date_part = re.sub(r'^(завтра|сегодня|послезавтра)\s+', '', date_part, flags=re.IGNORECASE)
        return date_part if date_part else None
    return None

def extract_venue_from_description(description):
    if not description:
        return None

    parts = description.split('•')
    if len(parts) > 1:
        venue = parts[1].strip()
        return venue if venue else None
    return None

def format_date(event):
    if 'dates' in event and event['dates']:
        dates = event['dates']
        if isinstance(dates, list) and len(dates) > 0:
            dates_str = ', '.join(dates[:3])
            if len(dates) > 3:
                dates_str += f' (+{len(dates) - 3} ещё)'
            return dates_str

    if 'date' in event and event['date']:
        return event['date']

    if 'description' in event and event['description']:
        date_from_desc = extract_date_from_description(event['description'])
        if date_from_desc:
            return date_from_desc

    return 'N/A'

def format_price(event):
    if 'prices' in event and event['prices']:
        prices = event['prices']
        if isinstance(prices, list) and len(prices) > 0:
            prices_str = ', '.join(prices)
            return prices_str

    if 'price' in event and event['price']:
        return event['price']

    return 'N/A'

def format_venue(event):
    if 'venue' in event and event['venue']:
        return event['venue']

    if 'description' in event and event['description']:
        venue_from_desc = extract_venue_from_description(event['description'])
        if venue_from_desc:
            return venue_from_desc

    return 'N/A'

async def main():
    try:
        print_separator()
        print("Yandex Afisha - Data Viewer")
        print_separator()

        try:
            async with async_session_maker() as session:
                await session.execute(select(1))
            print("✓ Connected to PostgreSQL")
        except OperationalError as e:
            print("\n❌ Error: Cannot connect to PostgreSQL!")
            print(f"Error: {e}")
            print("Make sure PostgreSQL is running:")
            print("  docker-compose up -d postgres")
            sys.exit(1)

        repository = ConcertRepository()

        total_events = await repository.count_events()
        print(f"\n📊 Total events in database: {total_events}\n")

        if total_events == 0:
            print("No events found. Run the parser first!")
            await repository.close()
            await close_db()
            return

        print_separator("-")
        print("Events by category:")
        print_separator("-")

        async with async_session_maker() as session:
            result = await session.execute(
                select(distinct(Event.category)).where(Event.category.isnot(None))
            )
            categories = [row[0] for row in result.all() if row[0]]

        for category in sorted(categories):
            count = await repository.count_events_by_category(category)
            print(f"  {category.ljust(20)}: {count} events")

        print(f"\n")
        print_separator("-")
        print("Sample events (latest 5):")
        print_separator("-")

        async with async_session_maker() as session:
            result = await session.execute(
                select(Event)
                .order_by(Event.scraped_at.desc())
                .limit(5)
            )
            sample_events = result.scalars().all()

        for i, event in enumerate(sample_events, 1):
            event_dict = event.to_dict()
            print(f"\n{i}. {event_dict.get('title', 'No title')}")
            print(f"   Category: {event_dict.get('category', 'N/A')}")
            print(f"   Date: {format_date(event_dict)}")
            print(f"   Venue: {format_venue(event_dict)}")
            print(f"   Price: {format_price(event_dict)}")
            print(f"   URL: {event_dict.get('url', 'N/A')}")

        print("\n")
        print_separator()
        print("To view all data, connect to PostgreSQL:")
        print(f"  psql -h {config.DB_HOST} -U {config.DB_USERNAME} -d {config.DB_NAME}")
        print("  > SELECT * FROM events ORDER BY scraped_at DESC LIMIT 10;")
        print_separator()

        await repository.close()
        await close_db()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())

