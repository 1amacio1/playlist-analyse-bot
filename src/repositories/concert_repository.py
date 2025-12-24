from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from src.db.models import Event
from src.db.database import async_session_maker

logger = logging.getLogger(__name__)

class ConcertRepository:
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> AsyncSession:
        if self._session:
            return self._session
        return async_session_maker()

    async def _close_session(self, session: AsyncSession):
        if self._own_session and session:
            await session.close()

    async def save_event(self, event_data: Dict) -> bool:
        session = await self._get_session()
        try:
            event = Event.from_dict(event_data)
            event.scraped_at = datetime.now(timezone.utc)

            session.add(event)
            await session.commit()
            logger.info(f"Saved event: {event_data.get('title', 'Unknown')}")
            return True
        except IntegrityError:
            await session.rollback()
            logger.debug(f"Duplicate event skipped: {event_data.get('url', 'Unknown')}")
            return False
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving event: {e}")
            return False
        finally:
            await self._close_session(session)

    async def save_events_batch(self, events: List[Dict]) -> int:
        saved_count = 0
        session = await self._get_session()
        try:
            for event_data in events:
                try:
                    url = event_data.get('url')
                    if not url:
                        logger.warning("Skipping event without URL")
                        continue

                    existing = await session.execute(
                        select(Event).where(Event.url == url)
                    )
                    if existing.scalar_one_or_none():
                        logger.debug(f"Duplicate event skipped: {url}")
                        continue

                    event = Event.from_dict(event_data)
                    event.scraped_at = datetime.now(timezone.utc)
                    session.add(event)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error processing event {event_data.get('url', 'Unknown')}: {e}")
                    continue

            await session.commit()
            logger.info(f"Saved {saved_count} events in batch")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in batch save: {e}", exc_info=True)
        finally:
            await self._close_session(session)

        return saved_count

    async def get_event_by_url(self, url: str) -> Optional[Dict]:
        session = await self._get_session()
        try:
            result = await session.execute(
                select(Event).where(Event.url == url)
            )
            event = result.scalar_one_or_none()
            return event.to_dict() if event else None
        except Exception as e:
            logger.error(f"Error getting event by URL: {e}")
            return None
        finally:
            await self._close_session(session)

    async def _get_events_by_category_async(self, category: str) -> List[Dict]:

        session = await self._get_session()
        try:
            result = await session.execute(
                select(Event).where(Event.category == category)
            )
            events = result.scalars().all()
            return [event.to_dict() for event in events]
        except Exception as e:
            logger.error(f"Error getting events by category: {e}")
            return []
        finally:
            await self._close_session(session)

    async def get_all_events(self) -> List[Dict]:

        session = await self._get_session()
        try:
            result = await session.execute(select(Event))
            events = result.scalars().all()
            return [event.to_dict() for event in events]
        except Exception as e:
            logger.error(f"Error getting all events: {e}")
            return []
        finally:
            await self._close_session(session)

    async def count_events(self) -> int:

        session = await self._get_session()
        try:
            from sqlalchemy import func
            result = await session.execute(select(func.count(Event.id)))
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting events: {e}")
            return 0
        finally:
            await self._close_session(session)

    async def count_events_by_category(self, category: str) -> int:

        session = await self._get_session()
        try:
            from sqlalchemy import func
            result = await session.execute(
                select(func.count(Event.id)).where(Event.category == category)
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting events by category: {e}")
            return 0
        finally:
            await self._close_session(session)

    async def delete_all_events(self) -> int:

        session = await self._get_session()
        try:
            result = await session.execute(delete(Event))
            await session.commit()
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} events")
            return deleted_count
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting all events: {e}")
            return 0
        finally:
            await self._close_session(session)

    async def close(self):
        if self._session:
            await self._session.close()
        logger.info("Database connection closed")

    def connect(self):
        pass

    def get_events_by_category(self, category: str) -> List[Dict]:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return asyncio.run(self._get_events_by_category_async(category))
                except ImportError:
                    logger.warning("nest_asyncio not installed. Install it for better async support.")
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_events_by_category_async(category))
                        return future.result()
            else:
                return loop.run_until_complete(self._get_events_by_category_async(category))
        except RuntimeError:
            return asyncio.run(self._get_events_by_category_async(category))
