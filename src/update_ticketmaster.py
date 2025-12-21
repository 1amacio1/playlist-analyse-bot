# src/update_ticketmaster.py
import asyncio
from pymongo import MongoClient
from clients.global_concert_client import get_artist_events
import pandas as pd
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017/")
ARTISTS_DB = "artists_db"
ARTISTS_COLLECTION = "big_artists"
AFISHA_DB = "afisha_db"
AFISHA_COLLECTION = "events"

MAX_CONCURRENT = 1 

async def fetch_event(semaphore, artist):
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            events = await loop.run_in_executor(None, get_artist_events, artist)
            await asyncio.sleep(1.1)  
            return artist, events
        except Exception as e:
            print(f"Error fetching {artist}: {e}")
            return artist, []

async def main():
    client = MongoClient(MONGO_URI)
    artists_col = client[ARTISTS_DB][ARTISTS_COLLECTION]
    afisha_col = client[AFISHA_DB][AFISHA_COLLECTION]

    artists = list(artists_col.find())
    print(f"Found {len(artists)} artists in DB.")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [fetch_event(semaphore, artist_doc['artist_name']) for artist_doc in artists[:100]]

    results = await asyncio.gather(*tasks)
    total_events = 0

    for artist_name, events in results:
        for e in events:
            # преобразуем под структуру afisha_db.events
            doc = {
                "title": e.get("event_name", "-"),
                "url": e.get("url", "-"),
                "category": "concert",
                "description": f"{e.get('city', '-')}, {e.get('venue', '-')}",
                "date": e.get("datetime", "-"),
                "price": "-",
                "venue": e.get("venue", "-"),
                "image": "-",
                "scraped_at": e.get("fetched_at")
            }
            afisha_col.update_one({"url": doc["url"]}, {"$set": doc}, upsert=True)

        total_events += len(events)
        print(f"{artist_name}: {len(events)} events inserted/updated")

    print(f"Total events inserted/updated: {total_events}")

if __name__ == "__main__":
    asyncio.run(main())