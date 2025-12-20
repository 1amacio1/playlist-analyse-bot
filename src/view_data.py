#!/usr/bin/env python3
"""
Utility script to view parsed data from MongoDB
"""

import sys
import os
import re
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
src_path = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.repositories.concert_repository import ConcertRepository
from pymongo.errors import ConnectionFailure
import json


def print_separator(char="=", length=60):
    print(char * length)


def extract_date_from_description(description):
    """Извлекает дату из description (формат: '30 декабря, 17:00 • VK Stadium')"""
    if not description:
        return None
    
    # Разделяем по "•" - дата обычно в первой части
    parts = description.split('•')
    if parts and len(parts) > 0:
        date_part = parts[0].strip()
        # Убираем время, если есть (формат: "30 декабря, 17:00")
        date_part = re.sub(r',\s*\d{1,2}:\d{2}', '', date_part)
        # Убираем "завтра", "сегодня", "послезавтра" если есть
        date_part = re.sub(r'^(завтра|сегодня|послезавтра)\s+', '', date_part, flags=re.IGNORECASE)
        return date_part if date_part else None
    return None


def extract_venue_from_description(description):
    """Извлекает venue из description (формат: '30 декабря, 17:00 • VK Stadium')"""
    if not description:
        return None
    
    # Разделяем по "•" - venue обычно во второй части
    parts = description.split('•')
    if len(parts) > 1:
        venue = parts[1].strip()
        return venue if venue else None
    return None


def format_date(event):
    """Форматирует дату из различных полей события"""
    # Сначала проверяем массив dates (детальная информация)
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
    """Форматирует цену из различных полей события"""
    if 'prices' in event and event['prices']:
        prices = event['prices']
        if isinstance(prices, list) and len(prices) > 0:
            prices_str = ', '.join(prices)
            return prices_str

    if 'price' in event and event['price']:
        return event['price']
    
    return 'N/A'


def format_venue(event):
    """Форматирует venue из различных полей события"""
    if 'venue' in event and event['venue']:
        return event['venue']

    if 'description' in event and event['description']:
        venue_from_desc = extract_venue_from_description(event['description'])
        if venue_from_desc:
            return venue_from_desc
    
    return 'N/A'


def main():
    try:
        print_separator()
        print("Yandex Afisha - Data Viewer")
        print_separator()
        
        db = ConcertRepository()
        
        total_events = db.count_events()
        print(f"\n📊 Total events in database: {total_events}\n")
        
        if total_events == 0:
            print("No events found. Run the parser first!")
            return
        
        print_separator("-")
        print("Events by category:")
        print_separator("-")
        
        categories = db.events_collection.distinct("category")
        for category in sorted(categories):
            count = db.count_events_by_category(category)
            print(f"  {category.ljust(20)}: {count} events")
        
        print(f"\n")
        print_separator("-")
        print("Sample events (latest 5):")
        print_separator("-")
        
        sample_events = list(db.events_collection.find().sort("scraped_at", -1).limit(5))
        
        for i, event in enumerate(sample_events, 1):
            print(f"\n{i}. {event.get('title', 'No title')}")
            print(f"   Category: {event.get('category', 'N/A')}")
            print(f"   Date: {format_date(event)}")
            print(f"   Venue: {format_venue(event)}")
            print(f"   Price: {format_price(event)}")
            print(f"   URL: {event.get('url', 'N/A')}")
        
        print("\n")
        print_separator()
        print("To view all data, connect to MongoDB:")
        print("  docker exec -it afisha_mongodb mongosh -u admin -p password123")
        print("  > use afisha_db")
        print("  > db.events.find().pretty()")
        print_separator()
        
        db.close()
        
    except ConnectionFailure:
        print("\n❌ Error: Cannot connect to MongoDB!")
        print("Make sure MongoDB is running:")
        print("  docker-compose up mongodb")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

