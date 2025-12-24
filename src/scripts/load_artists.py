import pandas as pd
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.services.concert_service import ConcertMatcherService
from src.repositories.concert_repository import ConcertRepository
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017/")
DB_NAME = "artists_db"
COLLECTION_NAME = "big_artists"
CSV_FILE = src_path / "artists.csv"

def load_artists_from_csv():
    repository = ConcertRepository()
    matcher_service = ConcertMatcherService(repository)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    if not CSV_FILE.exists():
        print(f"Error: File {CSV_FILE} not found")
        return

    df = pd.read_csv(CSV_FILE, header=None, names=['artist_name'])

    artists = []
    for name in df['artist_name']:
        normalized = matcher_service.normalize_name(name)
        artists.append({
            "artist_name": name,
            "normalized": normalized,
            "last_checked": None
        })

    if artists:
        collection.delete_many({})
        collection.insert_many(artists)
    print(f"Inserted {len(artists)} artists into MongoDB.")

if __name__ == "__main__":
    load_artists_from_csv()

