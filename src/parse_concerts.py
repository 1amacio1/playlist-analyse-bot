#!/usr/bin/env python3
import sys
import time
import logging
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.clients.local_concert_client import AfishaSeleniumParser
from src.repositories.concert_repository import ConcertRepository
from src.config.settings import config
import nest_asyncio

nest_asyncio.apply()

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

# Интервал между запусками (в секундах) - по умолчанию 6 часов
DEFAULT_INTERVAL_HOURS = 6
DEFAULT_INTERVAL_SECONDS = 20


async def parse_city(city: str, db: ConcertRepository, parser: AfishaSeleniumParser) -> tuple:
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
        saved_count = await db.save_events_batch(events)
        
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


async def run_parsing_all_cities():
    """Run parsing for all cities"""
    db = None
    parser = None
    
    try:
        logger.info("Connecting to database...")
        db = ConcertRepository()
        initial_count = await db.count_events_by_category('concert')
        logger.info(f"Current concerts in database: {initial_count}")
        
        logger.info("Initializing parser...")
        parser = AfishaSeleniumParser(headless=config.HEADLESS)
        parser.start()
        
        total_events = 0
        total_saved = 0
        city_results = {}
        
        for i, city in enumerate(ALL_CITIES, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"City {i}/{len(ALL_CITIES)}: {city}")
            logger.info(f"{'=' * 60}")
            
            events_count, saved_count = await parse_city(city, db, parser)
            total_events += events_count
            total_saved += saved_count
            city_results[city] = {'events': events_count, 'saved': saved_count}
            
            # Пауза между городами (кроме последнего)
            if i < len(ALL_CITIES):
                delay = 5
                logger.info(f"Waiting {delay} seconds before next city...")
                time.sleep(delay)
        
        # Итоговая статистика
        final_count = await db.count_events_by_category('concert')
        logger.info("\n" + "=" * 60)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Cities parsed: {len(ALL_CITIES)}")
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
        raise
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        if parser:
            logger.info("Closing browser...")
            parser.close()
        
        if db:
            logger.info("Closing database...")
            await db.close()


async def run_scheduled_parsing(interval_seconds):
    """Run parsing periodically with specified interval"""
    logger.info("=" * 60)
    logger.info("Starting scheduled parsing mode")
    logger.info(f"Interval: {interval_seconds / 3600:.1f} hours ({interval_seconds} seconds)")
    logger.info(f"Cities to parse: {len(ALL_CITIES)}")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            logger.info("\n" + "=" * 60)
            logger.info(f"SCHEDULED RUN #{iteration}")
            logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            try:
                await run_parsing_all_cities()
                logger.info(f"\n✓ Run #{iteration} completed successfully")
            except KeyboardInterrupt:
                logger.info("\nScheduled parsing stopped by user")
                break
            except Exception as e:
                logger.error(f"\n✗ Run #{iteration} failed: {e}", exc_info=True)
                logger.info("Continuing with next scheduled run...")
            
            # Calculate next run time
            next_run = datetime.fromtimestamp(time.time() + interval_seconds)
            logger.info("\n" + "=" * 60)
            logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Waiting {interval_seconds / 3600:.1f} hours...")
            logger.info("=" * 60)
            
            # Wait for next iteration
            await asyncio.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scheduled parsing stopped by user")
        logger.info("=" * 60)


def main():
    """Parse concerts from Yandex Afisha"""
    parser = argparse.ArgumentParser(
        description='Parse concerts from Yandex Afisha',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Parse all cities once'
    )
    parser.add_argument(
        '--cities',
        type=str,
        nargs='+',
        help='Specific cities to parse (e.g., moscow spb orenburg)'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run parsing periodically (default: every 6 hours)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_INTERVAL_HOURS,
        help=f'Interval between runs in hours (default: {DEFAULT_INTERVAL_HOURS})'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all events from database'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("Yandex Afisha Concert Parser")
    logger.info("=" * 50)
    
    # Clear database option
    if args.clear:
        async def clear_db():
            db = ConcertRepository()
            total_events = await db.count_events()
            logger.info(f"Current events in database: {total_events}")
            
            if total_events == 0:
                logger.info("Database is already empty.")
                await db.close()
                return
            
            if not sys.stdin.isatty():
                deleted_count = await db.delete_all_events()
                logger.info(f"Deleted {deleted_count} events")
            else:
                confirmation = input("Type 'DELETE' to confirm deletion: ").strip()
                if confirmation == 'DELETE':
                    deleted_count = await db.delete_all_events()
                    logger.info(f"Deleted {deleted_count} events")
                else:
                    logger.info("Operation cancelled.")
            await db.close()
        
        asyncio.run(clear_db())
        return
    
    # Scheduled mode
    if args.schedule:
        interval_seconds = args.interval * 3600
        asyncio.run(run_scheduled_parsing(interval_seconds))
        return
    
    # Single run mode
    cities_to_parse = []
    
    if args.all:
        cities_to_parse = ALL_CITIES
        logger.info(f"Parsing all {len(ALL_CITIES)} cities")
    elif args.cities:
        cities_to_parse = args.cities
        logger.info(f"Parsing cities: {cities_to_parse}")
    elif not sys.stdin.isatty():
        # Non-interactive mode - default to all cities
        cities_to_parse = ALL_CITIES
        logger.info(f"Non-interactive mode: parsing all {len(ALL_CITIES)} cities")
    else:
        # Interactive mode
        print("\nOptions:")
        print("1. Parse concerts (enter city name or 'all')")
        print("2. Clear database (enter 'clear')")
        choice = input("Enter choice: ").strip().lower()
        
        if choice == 'clear':
            async def clear_db_interactive():
                db = ConcertRepository()
                total_events = await db.count_events()
                logger.info(f"Current events in database: {total_events}")
                
                if total_events == 0:
                    logger.info("Database is already empty.")
                    await db.close()
                    return
                
                confirmation = input("Type 'DELETE' to confirm deletion: ").strip()
                if confirmation == 'DELETE':
                    deleted_count = await db.delete_all_events()
                    logger.info(f"Deleted {deleted_count} events")
                else:
                    logger.info("Operation cancelled.")
                await db.close()
            
            asyncio.run(clear_db_interactive())
            return
        
        print("\nSelect parsing mode:")
        print("1. Single city (enter city name)")
        print("2. All cities (enter 'all')")
        mode_input = input("Enter choice: ").strip().lower()
        
        if mode_input == 'all':
            cities_to_parse = ALL_CITIES
            logger.info(f"Parsing all {len(ALL_CITIES)} cities")
        elif mode_input:
            cities_to_parse = [mode_input]
            logger.info(f"Parsing single city: {mode_input}")
        else:
            cities_to_parse = [config.CITY]
            logger.info(f"Using default city: {config.CITY}")
    
    # Run parsing for specified cities
    async def run_parsing():
        db = None
        parser = None
        
        try:
            logger.info("Connecting to database...")
            db = ConcertRepository()
            initial_count = await db.count_events_by_category('concert')
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
                
                events_count, saved_count = await parse_city(city, db, parser)
                total_events += events_count
                total_saved += saved_count
                city_results[city] = {'events': events_count, 'saved': saved_count}
                
                if i < len(cities_to_parse):
                    delay = 5
                    logger.info(f"Waiting {delay} seconds before next city...")
                    time.sleep(delay)
            
            final_count = await db.count_events_by_category('concert')
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
            
            logger.info("\nResults by city:")
            for city, results in city_results.items():
                logger.info(f"  {city}: {results['events']} found, {results['saved']} saved")
            
        except KeyboardInterrupt:
            logger.info("Parser interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            if parser:
                logger.info("Closing browser...")
                parser.close()
            
            if db:
                logger.info("Closing database...")
                await db.close()
            
            logger.info("Parser finished")
    
    asyncio.run(run_parsing())


if __name__ == '__main__':
    main()

