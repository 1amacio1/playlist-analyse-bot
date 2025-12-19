from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime
from typing import List, Dict, Optional
import logging
from .config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.events_collection = None
        self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                config.mongo_uri,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[config.MONGO_DB]
            self.events_collection = self.db['events']
            self._create_indexes()
            logger.info(f"Successfully connected to MongoDB at {config.MONGO_HOST}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Create unique index on event URL to prevent duplicates
            self.events_collection.create_index([('url', ASCENDING)], unique=True)
            # Create index on category for filtering
            self.events_collection.create_index([('category', ASCENDING)])
            # Create index on date
            self.events_collection.create_index([('date', ASCENDING)])
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def save_event(self, event_data: Dict) -> bool:
        """
        Save a single event to database
        Returns True if saved, False if duplicate
        """
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
        """
        Save multiple events to database
        Returns count of successfully saved events
        """
        saved_count = 0
        for event in events:
            if self.save_event(event):
                saved_count += 1
        return saved_count

    def get_event_by_url(self, url: str) -> Optional[Dict]:
        """Get event by URL"""
        return self.events_collection.find_one({'url': url})

    def get_events_by_category(self, category: str) -> List[Dict]:
        """Get all events in a category"""
        return list(self.events_collection.find({'category': category}))

    def get_all_events(self) -> List[Dict]:
        """Get all events"""
        return list(self.events_collection.find())

    def count_events(self) -> int:
        """Get total count of events"""
        return self.events_collection.count_documents({})

    def count_events_by_category(self, category: str) -> int:
        """Get count of events in a category"""
        return self.events_collection.count_documents({'category': category})

    def delete_all_events(self):
        """Delete all events from database"""
        result = self.events_collection.delete_many({})
        logger.info(f"Deleted {result.deleted_count} events")
        return result.deleted_count

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

