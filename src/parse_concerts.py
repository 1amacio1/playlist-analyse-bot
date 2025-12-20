#!/usr/bin/env python3
"""
Script to parse concerts from Yandex Afisha and save to MongoDB
Run this before using the main playlist analyzer
"""

import sys
import time
import logging
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
src_path = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.clients.local_concert_client import AfishaSeleniumParser
from src.repositories.concert_repository import ConcertRepository
from src.config.settings import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Список популярных городов для парсинга
ALL_CITIES = [
    'moscow',
    'saint-petersburg',
    'yekaterinburg',
    'novosibirsk',
    'kazan',
    'nizhny-novgorod',
    'chelyabinsk',
    'samara',
    'orenburg'
]


def parse_city(city: str, db: ConcertRepository, parser: AfishaSeleniumParser) -> tuple:
    """Parse concerts for a single city"""
    logger.info("=" * 60)
    logger.info(f"Parsing city: {city}")
    logger.info("=" * 60)
    
    config.CITY = city
    
    try:
        try:
            parser.driver.current_url
        except Exception:
            logger.warning("Browser session lost, restarting...")
            parser.close()
            parser.start()
        
        start_time = time.time()
        events = parser.parse_all_events()
        
        if not events:
            logger.warning(f"No concerts were parsed for {city}!")
            return 0, 0
        
        logger.info(f"Saving {len(events)} concerts to database...")
        saved_count = db.save_events_batch(events)
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"City: {city}")
        logger.info(f"Total concerts found: {len(events)}")
        logger.info(f"New concerts saved: {saved_count}")
        logger.info(f"Duplicates skipped: {len(events) - saved_count}")
        logger.info(f"Time elapsed: {elapsed_time:.2f}s")
        
        return len(events), saved_count
        
    except Exception as e:
        error_msg = str(e)
        if 'invalid session id' in error_msg.lower():
            logger.warning(f"Browser session lost for {city}, will restart for next city")
            try:
                parser.close()
            except:
                pass
        logger.error(f"Error parsing city {city}: {e}", exc_info=True)
        return 0, 0


def main():
    """Parse concerts from Yandex Afisha"""
    logger.info("=" * 50)
    logger.info("Yandex Afisha Concert Parser")
    logger.info("=" * 50)
    
    # Опция очистки базы
    print("\nOptions:")
    print("1. Parse concerts (enter city name or 'all')")
    print("2. Clear database (enter 'clear')")
    choice = input("Enter choice: ").strip().lower()
    
    if choice == 'clear':
        db = ConcertRepository()
        total_events = db.count_events()
        logger.info(f"Current events in database: {total_events}")
        
        if total_events == 0:
            logger.info("Database is already empty.")
            db.close()
            return
        
        confirmation = input("Type 'DELETE' to confirm deletion: ").strip()
        if confirmation == 'DELETE':
            deleted_count = db.delete_all_events()
            logger.info(f"Deleted {deleted_count} events")
        else:
            logger.info("Operation cancelled.")
        db.close()
        return
    
    # Запрос режима парсинга
    print("\nSelect parsing mode:")
    print("1. Single city (enter city name)")
    print("2. All cities (enter 'all')")
    mode_input = input("Enter choice: ").strip().lower()
    
    cities_to_parse = []
    
    if mode_input == 'all':
        cities_to_parse = ALL_CITIES
        logger.info(f"Parsing all {len(ALL_CITIES)} cities")
    elif mode_input:
        cities_to_parse = [mode_input]
        logger.info(f"Parsing single city: {mode_input}")
    else:
        cities_to_parse = [config.CITY]
        logger.info(f"Using default city: {config.CITY}")
    
    db = None
    parser = None
    
    try:
        logger.info("Connecting to database...")
        db = ConcertRepository()
        initial_count = db.count_events_by_category('concert')
        logger.info(f"Current concerts in database: {initial_count}")
        
        logger.info("Initializing parser...")
        parser = AfishaSeleniumParser(headless=config.HEADLESS)
        parser.start()
        
        total_events = 0
        total_saved = 0
        city_results = {}
        
        for i, city in enumerate(cities_to_parse, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"City {i}/{len(cities_to_parse)}: {city}")
            logger.info(f"{'=' * 60}")
            
            events_count, saved_count = parse_city(city, db, parser)
            total_events += events_count
            total_saved += saved_count
            city_results[city] = {'events': events_count, 'saved': saved_count}
            
            # Пауза между городами (кроме последнего)
            if i < len(cities_to_parse):
                delay = 5
                logger.info(f"Waiting {delay} seconds before next city...")
                time.sleep(delay)
        
        # Итоговая статистика
        final_count = db.count_events_by_category('concert')
        logger.info("\n" + "=" * 60)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Cities parsed: {len(cities_to_parse)}")
        logger.info(f"Total events found: {total_events}")
        logger.info(f"Total new events saved: {total_saved}")
        logger.info(f"Total duplicates skipped: {total_events - total_saved}")
        logger.info(f"Initial concerts in database: {initial_count}")
        logger.info(f"Final concerts in database: {final_count}")
        logger.info(f"New concerts added: {final_count - initial_count}")
        logger.info("=" * 60)
        
        # Статистика по городам
        logger.info("\nResults by city:")
        for city, results in city_results.items():
            logger.info(f"  {city}: {results['events']} found, {results['saved']} saved")
        
    except KeyboardInterrupt:
        logger.info("Parser interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if parser:
            logger.info("Closing browser...")
            parser.close()
        
        if db:
            logger.info("Closing database...")
            db.close()
        
        logger.info("Parser finished")


if __name__ == '__main__':
    main()

