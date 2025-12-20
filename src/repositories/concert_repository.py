from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime
from typing import List, Dict, Optional
import logging
from src.config.settings import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConcertRepository:
    def __init__(self):
        self.client = None
        self.db = None
        self.events_collection = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(
                config.mongo_uri,
                serverSelectionTimeoutMS=5000
            )
            self.client.admin.command('ping')
            self.db = self.client[config.MONGO_DB]
            self.events_collection = self.db['events']
            self._create_indexes()
            logger.info(f"Successfully connected to MongoDB at {config.MONGO_HOST}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        try:
            self.events_collection.create_index([('url', ASCENDING)], unique=True)
            self.events_collection.create_index([('category', ASCENDING)])
            self.events_collection.create_index([('date', ASCENDING)])
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def save_event(self, event_data: Dict) -> bool:
        try:
            event_data['scraped_at'] = datetime.utcnow()
            self.events_collection.insert_one(event_data)
            logger.info(f"Saved event: {event_data.get('title', 'Unknown')}")
            return True
        except DuplicateKeyError:
            logger.debug(f"Duplicate event skipped: {event_data.get('url', 'Unknown')}")
            return False
        except Exception as e:
            logger.error(f"Error saving event: {e}")
            return False

    def save_events_batch(self, events: List[Dict]) -> int:
        saved_count = 0
        for event in events:
            if self.save_event(event):
                saved_count += 1
        return saved_count

    def get_event_by_url(self, url: str) -> Optional[Dict]:
        return self.events_collection.find_one({'url': url})

    def get_events_by_category(self, category: str) -> List[Dict]:
        return list(self.events_collection.find({'category': category}))

    def get_all_events(self) -> List[Dict]:
        return list(self.events_collection.find())

    def count_events(self) -> int:
        return self.events_collection.count_documents({})

    def count_events_by_category(self, category: str) -> int:
        return self.events_collection.count_documents({'category': category})

    def delete_all_events(self):
        result = self.events_collection.delete_many({})
        logger.info(f"Deleted {result.deleted_count} events")
        return result.deleted_count

    def close(self):
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
