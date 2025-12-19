#!/usr/bin/env python3
"""
Utility script to view parsed data from MongoDB
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
from pymongo.errors import ConnectionFailure
import json


def print_separator(char="=", length=60):
    print(char * length)


def main():
    try:
        print_separator()
        print("Yandex Afisha - Data Viewer")
        print_separator()
        
        db = Database()
        
        # Statistics
        total_events = db.count_events()
        print(f"\n📊 Total events in database: {total_events}\n")
        
        if total_events == 0:
            print("No events found. Run the parser first!")
            return
        
        # Events by category
        print_separator("-")
        print("Events by category:")
        print_separator("-")
        
        # Get all categories
        categories = db.events_collection.distinct("category")
        for category in sorted(categories):
            count = db.count_events_by_category(category)
            print(f"  {category.ljust(20)}: {count} events")
        
        # Sample events
        print(f"\n")
        print_separator("-")
        print("Sample events (latest 5):")
        print_separator("-")
        
        sample_events = list(db.events_collection.find().sort("scraped_at", -1).limit(5))
        
        for i, event in enumerate(sample_events, 1):
            print(f"\n{i}. {event.get('title', 'No title')}")
            print(f"   Category: {event.get('category', 'N/A')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Venue: {event.get('venue', 'N/A')}")
            print(f"   Price: {event.get('price', 'N/A')}")
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

