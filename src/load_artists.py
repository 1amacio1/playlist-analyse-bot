import pandas as pd
from pymongo import MongoClient
from services.concert_service import ConcertMatcherService
from repositories.concert_repository import ConcertRepository
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017/")
DB_NAME = "artists_db"
COLLECTION_NAME = "big_artists"
CSV_FILE = "artists.csv"


def load_artists_from_csv():
    repository = ConcertRepository()
    matcher_service = ConcertMatcherService(repository)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Читаем CSV без заголовка и задаём имя колонки
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
        collection.delete_many({})  # очистка старой коллекции
        collection.insert_many(artists)
    print(f"Inserted {len(artists)} artists into MongoDB.")


if __name__ == "__main__":
    load_artists_from_csv()