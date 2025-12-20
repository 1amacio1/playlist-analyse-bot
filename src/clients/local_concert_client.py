"""
Selenium-based scraper for Yandex Afisha
Uses undetected-chromedriver to avoid bot detection
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict, Optional
import logging
import time
import random
from datetime import datetime
from src.config.settings import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AfishaSeleniumParser:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def start(self):
        """Start Chrome with undetected-chromedriver"""
        logger.info("Starting Chrome with undetected-chromedriver...")

        import undetected_chromedriver as uc
        
        options = uc.ChromeOptions()

        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome'
        ]
        
        chrome_binary = None
        import os
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                logger.info(f"Found Chrome at: {chrome_binary}")
                break
        
        if chrome_binary:
            options.binary_location = chrome_binary
        else:
            logger.warning("Chrome binary not found, using default")
        
        options.add_argument(f'user-agent={config.USER_AGENT}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=ru-RU')
        
        if self.headless:
            options.add_argument('--headless=new')

        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
            self.driver.set_page_load_timeout(60)
            
            logger.info("Chrome started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome: {e}")
            raise

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
        logger.info("Browser closed")

    def human_like_delay(self, min_sec=1, max_sec=3):
        """Add random human-like delay"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def close_popups(self):
        """Close any popups or overlays"""
        try:
            self.human_like_delay(1, 2)

            # Try to find and close popup
            close_buttons = [
                '//button[@aria-label="Закрыть"]',
                '//button[contains(text(), "Закрыть")]',
            ]

            for xpath in close_buttons:
                try:
                    button = self.driver.find_element(By.XPATH, xpath)
                    button.click()
                    logger.info("Closed popup")
                    self.human_like_delay(0.5, 1)
                    break
                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.debug(f"No popups to close: {e}")

    def scroll_page(self, scrolls: int = 5):
        """Scroll page with human-like behavior"""
        for i in range(scrolls):
            # Random scroll position
            scroll_to = random.randint(300, 800)
            self.driver.execute_script(f'window.scrollTo(0, {scroll_to})')
            self.human_like_delay(0.5, 1.5)

            # Scroll to bottom
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            self.human_like_delay(1, 2)
            logger.debug(f"Scroll {i + 1}/{scrolls}")

    def get_categories(self) -> List[Dict]:
        """Extract available event categories"""
        logger.info("Extracting categories...")
        categories = []

        try:
            self.human_like_delay(3, 5)

            # Try to find category links
            category_selectors = [
                '//a[contains(@href, "/orenburg/")]',
                '//nav//a[contains(@href, "/orenburg/")]',
                '//header//a[contains(@href, "/orenburg/")]',
            ]

            for selector in category_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logger.debug(f"Found {len(elements)} elements with selector")

                    if len(elements) > 3:
                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                text = element.text.strip()

                                if not href or not text:
                                    continue

                                # Skip non-category links
                                if any(skip in href for skip in ['selections', 'places', 'media', 'filters']):
                                    continue

                                # Extract category name
                                if '/orenburg/' in href:
                                    parts = href.split('/orenburg/')
                                    if len(parts) > 1:
                                        category_name = parts[1].split('?')[0].strip('/')

                                        if category_name and category_name not in [c['name'] for c in categories]:
                                            categories.append({
                                                'name': category_name,
                                                'title': text,
                                                'url': href
                                            })
                            except Exception as e:
                                logger.debug(f"Error processing element: {e}")
                                continue

                        if len(categories) > 5:
                            break

                except Exception as e:
                    logger.debug(f"Selector failed: {e}")
                    continue

            # Use default categories if none found
            if len(categories) < 3:
                logger.warning("Using default categories")
                default_categories = [
                    ('cinema', 'Кино'),
                    ('theatre', 'Театр'),
                    ('concert', 'Концерты'),
                    ('standup', 'Стендап'),
                    ('exhibition', 'Выставки'),
                    ('kids', 'Детям'),
                ]
                categories = [
                    {
                        'name': name,
                        'title': title,
                        'url': f'{config.BASE_URL}/{name}?source=menu'
                    }
                    for name, title in default_categories
                ]

            logger.info(f"Found {len(categories)} categories: {[c['name'] for c in categories]}")
            return categories

        except Exception as e:
            logger.error(f"Error extracting categories: {e}")
            return []

    def get_selections(self, category: str) -> List[Dict]:
        """
        Get selection (subcategory) URLs for a category
        Returns list of {'name': str, 'url': str}
        """
        try:
            logger.debug(f"Finding selections for category: {category}")
            selections = []

            # Find selection links
            selection_elements = self.driver.find_elements(
                By.XPATH,
                f'//a[contains(@href, "/selections/") and contains(@href, "{category}")]'
            )

            logger.debug(f"Found {len(selection_elements)} selection links")

            for elem in selection_elements:
                try:
                    href = elem.get_attribute('href')
                    if not href:
                        continue

                    # Get title
                    try:
                        h2 = elem.find_element(By.XPATH, './/h2')
                        name = h2.text.strip()
                    except:
                        name = elem.text.strip() or "Selection"

                    if href and name:
                        selections.append({
                            'name': name,
                            'url': href
                        })
                        logger.debug(f"  Found selection: {name} -> {href[:50]}...")

                except Exception as e:
                    logger.debug(f"Error processing selection element: {e}")
                    continue

            # Limit number of selections
            if config.MAX_SELECTIONS_PER_CATEGORY and len(selections) > config.MAX_SELECTIONS_PER_CATEGORY:
                selections = selections[:config.MAX_SELECTIONS_PER_CATEGORY]
                logger.info(f"Limited to {config.MAX_SELECTIONS_PER_CATEGORY} selections")

            logger.info(f"Found {len(selections)} selections for {category}: {[s['name'] for s in selections]}")
            return selections

        except Exception as e:
            logger.error(f"Error getting selections: {e}")
            return []

    def parse_event_details(self, event_url: str) -> Dict:
        """
        Parse detailed information from individual event page
        Returns dict with description, schedule, prices, etc.
        """
        try:
            logger.debug(f"Parsing event details: {event_url}")

            # Navigate to event page
            self.driver.get(event_url)
            self.human_like_delay(2, 3)

            details = {}

            # H1 title
            try:
                h1 = self.driver.find_element(By.XPATH, '//h1')
                details['full_title'] = h1.text.strip()
            except:
                pass

            # Description
            try:
                # Try different selectors for description
                desc_selectors = [
                    '//div[@data-test-id="event.description"]',
                    '//div[contains(@class, "Description")]//p',
                    '//div[contains(@class, "description")]',
                ]

                for selector in desc_selectors:
                    try:
                        desc_elem = self.driver.find_element(By.XPATH, selector)
                        text = desc_elem.text.strip()
                        if text and len(text) > 50:
                            details['full_description'] = text[:2000]  # Limit length
                            break
                    except:
                        continue
            except:
                pass

            # Prices
            try:
                price_elements = self.driver.find_elements(
                    By.XPATH,
                    '//*[contains(@data-test-id, "price") and contains(text(), "₽")]'
                )
                if price_elements:
                    prices = [p.text.strip() for p in price_elements if '₽' in p.text]
                    details['prices'] = prices[:10]  # Limit number of prices
            except:
                pass

            # Schedule/dates
            try:
                schedule_elem = self.driver.find_element(
                    By.XPATH,
                    '//*[contains(@data-test-id, "schedule")]'
                )
                if schedule_elem:
                    details['has_schedule'] = True
            except:
                pass

            # Times
            try:
                time_elements = self.driver.find_elements(By.XPATH, '//time')
                if time_elements:
                    dates = []
                    for time_elem in time_elements[:10]:  # Limit
                        datetime_attr = time_elem.get_attribute('datetime')
                        text = time_elem.text.strip()
                        if datetime_attr or text:
                            dates.append(datetime_attr or text)
                    if dates:
                        details['dates'] = dates
            except:
                pass

            logger.debug(f"Extracted details: {list(details.keys())}")
            return details

        except Exception as e:
            logger.error(f"Error parsing event details: {e}")
            return {}

    def check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present"""
        try:
            page_source = self.driver.page_source
            if 'Я не робот' in page_source or 'SmartCaptcha' in page_source:
                return True
            return False
        except:
            return False

    def wait_for_captcha_solution(self, max_wait_seconds=120, skip_if_headless=True):
        """
        Wait for user to solve CAPTCHA manually
        Returns True if CAPTCHA was solved, False if timeout or skipped
        """
        if not self.check_for_captcha():
            return True  # No CAPTCHA, continue

        # Если headless режим и опция пропуска включена - просто пропускаем
        if skip_if_headless and self.headless:
            logger.warning("=" * 60)
            logger.warning("🔴 CAPTCHA ОБНАРУЖЕНА (headless режим)")
            logger.warning("⏭️  Пропускаю страницу с CAPTCHA")
            logger.warning("=" * 60)
            return False  # Пропускаем страницу

        logger.warning("=" * 60)
        logger.warning("🔴 CAPTCHA ОБНАРУЖЕНА!")
        logger.warning("=" * 60)
        logger.warning(f"⏰ Ожидание {max_wait_seconds} секунд...")
        logger.warning("📝 Решите CAPTCHA в открытом браузере")
        logger.warning("✅ Парсер продолжит автоматически после решения")
        logger.warning("=" * 60)

        import time
        start_time = time.time()
        check_interval = 2

        while time.time() - start_time < max_wait_seconds:
            if not self.check_for_captcha():
                elapsed = int(time.time() - start_time)
                logger.info("=" * 60)
                logger.info(f"✅ CAPTCHA решена за {elapsed} секунд!")
                logger.info("🚀 Продолжаю парсинг...")
                logger.info("=" * 60)
                time.sleep(2)
                return True

            elapsed = int(time.time() - start_time)
            remaining = max_wait_seconds - elapsed
            if elapsed % 10 == 0:
                logger.info(f"⏳ Ожидание... Осталось ~{remaining} сек")

            time.sleep(check_interval)

        logger.error("=" * 60)
        logger.error(f"⏰ Таймаут {max_wait_seconds} секунд истек")
        logger.error("❌ CAPTCHA не была решена")
        logger.error("=" * 60)
        return False

    def parse_events_from_page(self, category: str) -> List[Dict]:
        """Parse events from current page"""
        events = []

        try:
            self.human_like_delay(5, 8)  # Увеличиваем задержку

            # Check for CAPTCHA and wait for solution
            if self.check_for_captcha():
                # Сохраняем скриншот
                try:
                    import os
                    from pathlib import Path
                    if os.path.exists('/app/logs'):
                        screenshot_path = f'/app/logs/captcha_{category}_{int(time.time())}.png'
                    else:
                        log_dir = Path(__file__).parent.parent / 'logs'
                        log_dir.mkdir(exist_ok=True)
                        screenshot_path = str(log_dir / f'captcha_{category}_{int(time.time())}.png')

                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.debug(f"Could not save screenshot: {e}")

                # В headless режиме пробуем перезагрузить страницу после задержки
                if self.headless:
                    logger.warning("CAPTCHA detected in headless mode, waiting and retrying...")
                    time.sleep(10)  # Ждем 10 секунд
                    self.driver.refresh()  # Перезагружаем страницу
                    self.human_like_delay(5, 8)
                    
                    # Проверяем снова
                    if self.check_for_captcha():
                        logger.warning(f"⏭️  Пропускаю страницу с CAPTCHA для категории: {category}")
                        return events
                
                # Wait for user to solve CAPTCHA
                if not self.wait_for_captcha_solution(max_wait_seconds=120, skip_if_headless=True):
                    logger.warning(f"⏭️  Пропускаю страницу с CAPTCHA для категории: {category}")
                    return events

                # CAPTCHA solved, continue
                self.human_like_delay(2, 3)

            # Click "Show more" buttons to load all events
            logger.info("Clicking 'Show more' buttons to load all events...")
            max_clicks = 15  # Максимум кликов
            clicks_made = 0

            for click_num in range(max_clicks):
                try:
                    # Find "Show more" button
                    show_more_button = self.driver.find_element(
                        By.XPATH,
                        '//button[@data-test-id="eventsList.more" or contains(text(), "Показать ещё")]'
                    )

                    if show_more_button.is_displayed() and show_more_button.is_enabled():
                        # Scroll to button
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                        self.human_like_delay(0.5, 1)

                        # Click
                        show_more_button.click()
                        clicks_made += 1
                        logger.debug(f"Clicked 'Show more' button ({clicks_made}/{max_clicks})")

                        # Wait for content to load
                        self.human_like_delay(1, 2)
                    else:
                        break
                except:
                    # No more "Show more" buttons
                    break

            if clicks_made > 0:
                logger.info(f"✓ Clicked 'Show more' {clicks_made} times")

            # Scroll to load lazy images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_like_delay(1, 2)

            # Find event elements - multiple strategies
            event_elements = []

            # CORRECT selectors based on real Yandex Afisha structure
            # Events are in cards with class DggLY9
            xpath_selectors = [
                # Основной способ: карточки событий
                '//div[@class="DggLY9"]',
                # Fallback: любые элементы с data-test-id для событий
                '//a[@data-test-id="eventCard.link"]',
            ]

            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    logger.debug(f"XPath '{xpath}': found {len(elements)} elements")

                    if len(elements) >= 3:
                        event_elements = elements
                        logger.info(f"Using XPath '{xpath}': found {len(elements)} event elements")
                        break
                except Exception as e:
                    logger.debug(f"XPath {xpath} failed: {e}")
                    continue

            if not event_elements:
                logger.warning(f"No events found for category: {category}")
                # Save screenshot for debugging
                try:
                    import os
                    from pathlib import Path
                    if os.path.exists('/app/logs'):
                        screenshot_path = f'/app/logs/debug_{category}_{int(time.time())}.png'
                    else:
                        log_dir = Path(__file__).parent.parent / 'logs'
                        log_dir.mkdir(exist_ok=True)
                        screenshot_path = str(log_dir / f'debug_{category}_{int(time.time())}.png')

                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved debug screenshot: {screenshot_path}")
                except Exception as e:
                    logger.debug(f"Could not save screenshot: {e}")
                return events

            # Track unique URLs to avoid duplicates
            seen_urls = set()

            # Parse each event
            for idx, element in enumerate(event_elements[:50]):
                try:
                    event_data = self._extract_event_data(element, category)
                    if event_data and event_data.get('url'):
                        # Skip if already seen
                        if event_data['url'] in seen_urls:
                            logger.debug(f"Skipping duplicate URL: {event_data['url']}")
                            continue

                        seen_urls.add(event_data['url'])
                        events.append(event_data)
                        logger.info(f"✓ [{len(events)}] {event_data.get('title', 'No title')[:60]}")
                except Exception as e:
                    logger.debug(f"Error parsing element {idx}: {e}")
                    continue

            logger.info(f"Successfully parsed {len(events)} events from category: {category}")

        except Exception as e:
            logger.error(f"Error parsing events: {e}", exc_info=True)

        return events

    def _extract_event_data(self, element, category: str) -> Optional[Dict]:
        """Extract event data from Yandex Afisha event card (DggLY9 structure)"""
        try:
            tag_name = element.tag_name.lower()
            title = None
            url = None
            description = None
            image_url = None

            # Case 1: Element is event card DIV (DggLY9)
            if tag_name == 'div':
                # Find title: <h2 data-test-id="eventCard.eventInfoTitle">
                try:
                    h2 = element.find_element(By.XPATH, './/h2[@data-test-id="eventCard.eventInfoTitle"]')
                    title = h2.text.strip()
                except:
                    # Try any h2
                    try:
                        h2 = element.find_element(By.XPATH, './/h2')
                        title = h2.text.strip()
                    except:
                        pass

                # Find link: <a data-test-id="eventCard.link">
                try:
                    link = element.find_element(By.XPATH, './/a[@data-test-id="eventCard.link"]')
                    url = link.get_attribute('href')
                except:
                    # Try any link
                    try:
                        link = element.find_element(By.XPATH, f'.//a[contains(@href, "/orenburg/{category}/")]')
                        url = link.get_attribute('href')
                    except:
                        pass

                # Find details: <ul data-test-id="eventCard.eventInfoDetails">
                try:
                    ul = element.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                    details = [li.text.strip() for li in ul.find_elements(By.XPATH, './/li')]
                    description = ' • '.join(details) if details else None
                except:
                    pass

                # Find image
                try:
                    img = element.find_element(By.XPATH, './/img')
                    image_url = img.get_attribute('src') or img.get_attribute('data-src')
                except:
                    pass

            # Case 2: Element is a link itself
            elif tag_name == 'a':
                url = element.get_attribute('href')

                # Try to find title in parent container
                try:
                    container = element.find_element(By.XPATH, './ancestor::div[@class="DggLY9"]')
                    h2 = container.find_element(By.XPATH, './/h2[@data-test-id="eventCard.eventInfoTitle"]')
                    title = h2.text.strip()

                    # Get details
                    try:
                        ul = container.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                        details = [li.text.strip() for li in ul.find_elements(By.XPATH, './/li')]
                        description = ' • '.join(details) if details else None
                    except:
                        pass

                    # Get image
                    try:
                        img = container.find_element(By.XPATH, './/img')
                        image_url = img.get_attribute('src') or img.get_attribute('data-src')
                    except:
                        pass
                except:
                    # Extract title from URL as fallback
                    if url:
                        parts = url.split('/')
                        for part in reversed(parts):
                            if part and part != 'orenburg' and category not in part:
                                name = part.split('?')[0]
                                if name and len(name) > 3:
                                    title = name.replace('-', ' ').replace('_', ' ').title()
                                    break

            # If still no title or URL
            else:
                return None

            # Skip if no title or URL
            if not title or not url or len(title) < 3:
                return None

            # Skip non-event links
            if any(x in url for x in ['/selections/', '/places/', '/filters']):
                return None

            # Use image_url if not already found
            if not image_url:
                try:
                    img = element.find_element(By.TAG_NAME, 'img')
                    image_url = img.get_attribute('src') or img.get_attribute('data-src')
                except:
                    pass

            # Use description if not already found
            if not description:
                try:
                    desc_elements = element.find_elements(By.XPATH, './/*[contains(@class, "description") or self::p]')
                    for desc in desc_elements:
                        text = desc.text.strip()
                        if text and len(text) > 10:
                            description = text
                            break
                except:
                    pass

            date_text = None
            try:
                date_elements = element.find_elements(By.XPATH,
                                                      './/*[contains(@class, "date") or contains(@class, "Date") or self::time]')
                if date_elements:
                    for date_elem in date_elements:
                        datetime_attr = date_elem.get_attribute('datetime')
                        if datetime_attr:
                            date_text = datetime_attr
                            break
                        text = date_elem.text.strip()
                        if text and len(text) > 0:
                            date_text = text
                            break

                if not date_text and url:
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
                    if date_match:
                        date_text = date_match.group(1)

                if not date_text:
                    try:
                        ul = element.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                        details = ul.find_elements(By.XPATH, './/li')
                        for li in details:
                            text = li.text.strip()
                            if text and any(char.isdigit() for char in text):
                                if any(month in text.lower() for month in ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) or re.search(r'\d{1,2}[\./\-]\d{1,2}', text):
                                    date_text = text
                                    break
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Error extracting date: {e}")

            # Extract price
            price = None
            try:
                price_selectors = [
                    './/*[contains(@class, "price") or contains(@class, "Price")]',
                    './/*[contains(text(), "₽")]',
                    './/*[contains(text(), "руб")]',
                ]
                
                for selector in price_selectors:
                    price_elements = element.find_elements(By.XPATH, selector)
                    if price_elements:
                        for price_elem in price_elements:
                            text = price_elem.text.strip()
                            # Проверяем, что это похоже на цену (содержит символ валюты или слово "руб")
                            if text and ('₽' in text or 'руб' in text.lower() or 'от' in text.lower()):
                                price = text
                                break
                        if price:
                            break

                if not price:
                    try:
                        ul = element.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                        details = ul.find_elements(By.XPATH, './/li')
                        for li in details:
                            text = li.text.strip()
                            if text and ('₽' in text or 'руб' in text.lower()):
                                price = text
                                break
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Error extracting price: {e}")

            # Extract venue
            venue = None
            try:
                venue_elements = element.find_elements(By.XPATH,
                                                       './/*[contains(@class, "venue") or contains(@class, "place") or contains(@class, "Venue") or contains(@class, "Place")]')
                if venue_elements:
                    venue = venue_elements[0].text.strip()
            except:
                pass

            return {
                'title': title[:500],
                'url': url,
                'category': category,
                'description': description[:1000] if description else None,
                'date': date_text,
                'price': price,
                'venue': venue,
                'image': image_url,
                'scraped_at': datetime.utcnow()
            }

        except Exception as e:
            logger.debug(f"Error extracting event data: {e}")
            return None

    def parse_category(self, category: Dict) -> List[Dict]:
        """Parse all events from a category (including selections)"""
        logger.info(f"Parsing category: {category['title']} ({category['url']})")

        all_events = []

        try:
            # Navigate to category
            self.driver.get(category['url'])
            self.human_like_delay(3, 5)

            # Check for CAPTCHA and wait for solution
            if self.check_for_captcha():
                # Wait for user to solve CAPTCHA
                if not self.wait_for_captcha_solution(max_wait_seconds=120, skip_if_headless=True):
                    logger.warning("⏭️  Пропускаю страницу с CAPTCHA")
                    return all_events  # Возвращаем пустой список, пропускаем эту категорию

                # CAPTCHA solved, continue
                self.human_like_delay(2, 3)

            # Close popups
            self.close_popups()

            # Simulate human reading
            self.human_like_delay(2, 4)

            # Scroll to load content
            self.scroll_page(scrolls=3)

            # Parse events from main category page
            main_events = self.parse_events_from_page(category['name'])
            all_events.extend(main_events)
            logger.info(f"  Main page: {len(main_events)} events")

            # Parse selections (subcategories) if enabled
            if config.PARSE_SELECTIONS:
                logger.info(f"  Looking for selections...")
                selections = self.get_selections(category['name'])

                if selections:
                    logger.info(f"  Found {len(selections)} selections, parsing...")

                    for sel_idx, selection in enumerate(selections, 1):
                        try:
                            logger.info(f"    Selection {sel_idx}/{len(selections)}: {selection['name']}")

                            # Navigate to selection
                            self.driver.get(selection['url'])
                            self.human_like_delay(2, 3)

                            # Check for CAPTCHA
                            if self.check_for_captcha():
                                if not self.wait_for_captcha_solution(max_wait_seconds=90, skip_if_headless=True):
                                    logger.warning("⏭️  Пропускаю страницу события с CAPTCHA")
                                    continue

                            # Parse events from selection
                            sel_events = self.parse_events_from_page(category['name'])
                            all_events.extend(sel_events)
                            logger.info(f"      → {len(sel_events)} events")

                            # Small delay between selections
                            if sel_idx < len(selections):
                                self.human_like_delay(2, 3)

                        except Exception as e:
                            logger.error(f"    Error parsing selection {selection['name']}: {e}")
                            continue
                else:
                    logger.info(f"  No selections found for {category['name']}")

            # Parse event details if enabled
            if config.PARSE_EVENT_DETAILS and all_events:
                logger.info(f"  Parsing event details for first {config.MAX_EVENTS_FOR_DETAILS} events...")
                events_to_detail = all_events[:config.MAX_EVENTS_FOR_DETAILS]

                for evt_idx, event in enumerate(events_to_detail, 1):
                    try:
                        logger.info(f"    Event {evt_idx}/{len(events_to_detail)}: {event['title'][:40]}...")

                        # Parse details
                        details = self.parse_event_details(event['url'])

                        # Merge details into event
                        if details:
                            event.update(details)
                            logger.debug(f"      Added details: {list(details.keys())}")

                        # Delay between detail requests
                        if evt_idx < len(events_to_detail):
                            self.human_like_delay(1, 2)

                    except Exception as e:
                        logger.error(f"    Error parsing details for {event['title']}: {e}")
                        continue

            return all_events

        except Exception as e:
            logger.error(f"Error parsing category {category['title']}: {e}", exc_info=True)
            return []

    def parse_all_events(self) -> List[Dict]:
        """Parse events from all categories"""
        all_events = []

        try:
            # Navigate to main page
            logger.info(f"Navigating to {config.BASE_URL}")
            self.driver.get(config.BASE_URL)
            self.human_like_delay(4, 6)

            # Check for CAPTCHA on main page
            if self.check_for_captcha():
                # Save screenshot
                try:
                    import os
                    from pathlib import Path
                    if os.path.exists('/app/logs'):
                        screenshot_path = f'/app/logs/captcha_main_{int(time.time())}.png'
                    else:
                        log_dir = Path(__file__).parent.parent / 'logs'
                        log_dir.mkdir(exist_ok=True)
                        screenshot_path = str(log_dir / f'captcha_main_{int(time.time())}.png')

                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.debug(f"Could not save screenshot: {e}")

                # Wait for user to solve CAPTCHA (3 minutes for main page)
                if not self.wait_for_captcha_solution(max_wait_seconds=180, skip_if_headless=True):
                    logger.error("Cannot continue - CAPTCHA not solved on main page")
                    # В headless режиме просто продолжаем, возможно получится на других страницах
                    if self.headless:
                        logger.warning("⏭️  Продолжаю в headless режиме, несмотря на CAPTCHA на главной странице")
                    else:
                        raise Exception("CAPTCHA не решена на главной странице")

                # CAPTCHA solved, continue
                self.human_like_delay(3, 5)

            # Close popups
            self.close_popups()

            # Get categories
            categories = self.get_categories()

            if not categories:
                logger.warning("No categories found")
                return []

            # Filter categories if configured
            categories_to_parse = categories

            # Filter by category names if specified
            if config.CATEGORIES_TO_PARSE:
                categories_to_parse = [
                    cat for cat in categories
                    if cat['name'] in config.CATEGORIES_TO_PARSE
                ]
                if not categories_to_parse:
                    logger.warning(f"No categories found matching: {config.CATEGORIES_TO_PARSE}")
                    logger.info(f"Available categories: {[c['name'] for c in categories]}")
                    return []
                logger.info(f"Filtered to categories: {[c['name'] for c in categories_to_parse]}")

            # Limit number of categories if configured
            if config.MAX_CATEGORIES and len(categories_to_parse) > config.MAX_CATEGORIES:
                categories_to_parse = categories_to_parse[:config.MAX_CATEGORIES]

            # Parse each category
            for idx, category in enumerate(categories_to_parse, 1):
                try:
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"Category {idx}/{len(categories_to_parse)}: {category['title']}")
                    logger.info(f"{'=' * 60}")

                    events = self.parse_category(category)
                    all_events.extend(events)
                    logger.info(f"✓ '{category['title']}': {len(events)} events")

                    # Delay between categories
                    if idx < len(categories_to_parse):
                        delay = random.uniform(
                            config.MIN_DELAY_BETWEEN_CATEGORIES,
                            config.MAX_DELAY_BETWEEN_CATEGORIES
                        )
                        logger.info(f"Waiting {delay:.1f}s...")
                        time.sleep(delay)

                except Exception as e:
                    logger.error(f"✗ Error: {category['title']}: {e}")
                    continue

            logger.info(f"\n{'=' * 60}")
            logger.info(f"✓ Total events: {len(all_events)}")
            logger.info(f"{'=' * 60}")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        return all_events

