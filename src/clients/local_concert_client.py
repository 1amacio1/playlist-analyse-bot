
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
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')

        if config.proxy_url:
            proxy_url = config.proxy_url
            options.add_argument(f'--proxy-server={proxy_url}')
            logger.info(f"Using proxy: {config.PROXY_HOST}:{config.PROXY_PORT}")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)

        import os
        driver_executable_path = None
        use_system_driver = os.path.exists('/.dockerenv')
        if use_system_driver:
            driver_executable_path = '/usr/bin/chromedriver'
            logger.info(f"Using system chromedriver: {driver_executable_path}")

        try:
            self.driver = uc.Chrome(
                options=options,
                version_main=None,
                driver_executable_path=driver_executable_path,
                use_subprocess=True
            )
            self.driver.set_page_load_timeout(60)

            logger.info("Chrome started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.quit()
        logger.info("Browser closed")

    def human_like_delay(self, min_sec=1, max_sec=3):
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def close_popups(self):
        try:
            self.human_like_delay(1, 2)

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
        for i in range(scrolls):
            scroll_to = random.randint(300, 800)
            self.driver.execute_script(f'window.scrollTo(0, {scroll_to})')
            self.human_like_delay(0.5, 1.5)

            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            self.human_like_delay(1, 2)
            logger.debug(f"Scroll {i + 1}/{scrolls}")

    def get_categories(self) -> List[Dict]:
        logger.info("Extracting categories...")
        categories = []

        try:
            self.human_like_delay(3, 5)

            current_city = config.CITY
            category_selectors = [
                f'//a[contains(@href, "/{current_city}/")]',
                f'//nav//a[contains(@href, "/{current_city}/")]',
                f'//header//a[contains(@href, "/{current_city}/")]',
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

                                if any(skip in href for skip in ['selections', 'places', 'media', 'filters']):
                                    continue

                                city_path = f'/{current_city}/'
                                if city_path in href:
                                    parts = href.split(city_path)
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
        try:
            logger.debug(f"Finding selections for category: {category}")
            selections = []

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

            if config.MAX_SELECTIONS_PER_CATEGORY and len(selections) > config.MAX_SELECTIONS_PER_CATEGORY:
                selections = selections[:config.MAX_SELECTIONS_PER_CATEGORY]
                logger.info(f"Limited to {config.MAX_SELECTIONS_PER_CATEGORY} selections")

            logger.info(f"Found {len(selections)} selections for {category}: {[s['name'] for s in selections]}")
            return selections

        except Exception as e:
            logger.error(f"Error getting selections: {e}")
            return []

    def parse_event_details(self, event_url: str) -> Dict:
        try:
            logger.debug(f"Parsing event details: {event_url}")

            self.driver.get(event_url)
            self.human_like_delay(2, 3)

            details = {}

            try:
                h1 = self.driver.find_element(By.XPATH, '//h1')
                details['full_title'] = h1.text.strip()
            except:
                pass

            try:
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
                            details['full_description'] = text[:2000]
                            break
                    except:
                        continue
            except:
                pass

            try:
                price_elements = self.driver.find_elements(
                    By.XPATH,
                    '//*[contains(@data-test-id, "price") and contains(text(), "₽")]'
                )
                if price_elements:
                    prices = [p.text.strip() for p in price_elements if '₽' in p.text]
                    details['prices'] = prices[:10]
            except:
                pass

            try:
                schedule_elem = self.driver.find_element(
                    By.XPATH,
                    '//*[contains(@data-test-id, "schedule")]'
                )
                if schedule_elem:
                    details['has_schedule'] = True
            except:
                pass

            try:
                time_elements = self.driver.find_elements(By.XPATH, '//time')
                if time_elements:
                    dates = []
                    for time_elem in time_elements[:10]:
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
        try:
            page_source = self.driver.page_source
            if 'Я не робот' in page_source or 'SmartCaptcha' in page_source:
                return True
            return False
        except:
            return False

    def wait_for_captcha_solution(self, max_wait_seconds=120, skip_if_headless=True):
        if not self.check_for_captcha():
            return True

        if skip_if_headless and self.headless:
            logger.warning("=" * 60)
            logger.warning("🔴 CAPTCHA ОБНАРУЖЕНА (headless режим)")
            logger.warning("⏭️  Пропускаю страницу с CAPTCHA")
            logger.warning("=" * 60)
            return False

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
        events = []

        try:
            self.human_like_delay(5, 8)

            if self.check_for_captcha():
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

                if self.headless:
                    logger.warning("CAPTCHA detected in headless mode, waiting and retrying...")
                    time.sleep(10)
                    self.driver.refresh()
                    self.human_like_delay(5, 8)

                    if self.check_for_captcha():
                        logger.warning(f"⏭️  Пропускаю страницу с CAPTCHA для категории: {category}")
                        return events

                if not self.wait_for_captcha_solution(max_wait_seconds=120, skip_if_headless=True):
                    logger.warning(f"⏭️  Пропускаю страницу с CAPTCHA для категории: {category}")
                    return events

                self.human_like_delay(2, 3)

            logger.info("Clicking 'Show more' buttons to load all events...")
            max_clicks = 15
            clicks_made = 0

            for click_num in range(max_clicks):
                try:
                    show_more_button = self.driver.find_element(
                        By.XPATH,
                        '//button[@data-test-id="eventsList.more" or contains(text(), "Показать ещё")]'
                    )

                    if show_more_button.is_displayed() and show_more_button.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                        self.human_like_delay(0.5, 1)

                        show_more_button.click()
                        clicks_made += 1
                        logger.debug(f"Clicked 'Show more' button ({clicks_made}/{max_clicks})")

                        self.human_like_delay(1, 2)
                    else:
                        break
                except:
                    break

            if clicks_made > 0:
                logger.info(f"✓ Clicked 'Show more' {clicks_made} times")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_like_delay(1, 2)

            event_elements = []

            xpath_selectors = [
                '//div[@class="DggLY9"]',
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

            seen_urls = set()

            for idx, element in enumerate(event_elements[:50]):
                try:
                    event_data = self._extract_event_data(element, category)
                    if event_data and event_data.get('url'):
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
        try:
            tag_name = element.tag_name.lower()
            title = None
            url = None
            description = None
            image_url = None

            if tag_name == 'div':
                try:
                    h2 = element.find_element(By.XPATH, './/h2[@data-test-id="eventCard.eventInfoTitle"]')
                    title = h2.text.strip()
                except:
                    try:
                        h2 = element.find_element(By.XPATH, './/h2')
                        title = h2.text.strip()
                    except:
                        pass

                try:
                    link = element.find_element(By.XPATH, './/a[@data-test-id="eventCard.link"]')
                    url = link.get_attribute('href')
                except:
                    try:
                        link = element.find_element(By.XPATH, f'.//a[contains(@href, "/orenburg/{category}/")]')
                        url = link.get_attribute('href')
                    except:
                        pass

                try:
                    ul = element.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                    details = [li.text.strip() for li in ul.find_elements(By.XPATH, './/li')]
                    description = ' • '.join(details) if details else None
                except:
                    pass

                try:
                    img = element.find_element(By.XPATH, './/img')
                    image_url = img.get_attribute('src') or img.get_attribute('data-src')
                except:
                    pass

            elif tag_name == 'a':
                url = element.get_attribute('href')

                try:
                    container = element.find_element(By.XPATH, './ancestor::div[@class="DggLY9"]')
                    h2 = container.find_element(By.XPATH, './/h2[@data-test-id="eventCard.eventInfoTitle"]')
                    title = h2.text.strip()

                    try:
                        ul = container.find_element(By.XPATH, './/ul[@data-test-id="eventCard.eventInfoDetails"]')
                        details = [li.text.strip() for li in ul.find_elements(By.XPATH, './/li')]
                        description = ' • '.join(details) if details else None
                    except:
                        pass

                    try:
                        img = container.find_element(By.XPATH, './/img')
                        image_url = img.get_attribute('src') or img.get_attribute('data-src')
                    except:
                        pass
                except:
                    if url:
                        parts = url.split('/')
                        for part in reversed(parts):
                            if part and part != 'orenburg' and category not in part:
                                name = part.split('?')[0]
                                if name and len(name) > 3:
                                    title = name.replace('-', ' ').replace('_', ' ').title()
                                    break

            else:
                return None

            if not title or not url or len(title) < 3:
                return None

            if any(x in url for x in ['/selections/', '/places/', '/filters']):
                return None

            if not image_url:
                try:
                    img = element.find_element(By.TAG_NAME, 'img')
                    image_url = img.get_attribute('src') or img.get_attribute('data-src')
                except:
                    pass

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
                'city': config.CITY,
                'image': image_url,
                'scraped_at': datetime.utcnow()
            }

        except Exception as e:
            logger.debug(f"Error extracting event data: {e}")
            return None

    def parse_category(self, category: Dict) -> List[Dict]:
        logger.info(f"Parsing category: {category['title']} ({category['url']})")

        all_events = []

        try:
            self.driver.get(category['url'])
            self.human_like_delay(3, 5)

            if self.check_for_captcha():
                if not self.wait_for_captcha_solution(max_wait_seconds=120, skip_if_headless=True):
                    logger.warning("⏭️  Пропускаю страницу с CAPTCHA")
                    return all_events

                self.human_like_delay(2, 3)

            self.close_popups()

            self.human_like_delay(2, 4)

            self.scroll_page(scrolls=3)

            main_events = self.parse_events_from_page(category['name'])
            all_events.extend(main_events)
            logger.info(f"  Main page: {len(main_events)} events")

            if config.PARSE_SELECTIONS:
                logger.info(f"  Looking for selections...")
                selections = self.get_selections(category['name'])

                if selections:
                    logger.info(f"  Found {len(selections)} selections, parsing...")

                    for sel_idx, selection in enumerate(selections, 1):
                        try:
                            logger.info(f"    Selection {sel_idx}/{len(selections)}: {selection['name']}")

                            self.driver.get(selection['url'])
                            self.human_like_delay(2, 3)

                            if self.check_for_captcha():
                                if not self.wait_for_captcha_solution(max_wait_seconds=90, skip_if_headless=True):
                                    logger.warning("⏭️  Пропускаю страницу события с CAPTCHA")
                                    continue

                            sel_events = self.parse_events_from_page(category['name'])
                            all_events.extend(sel_events)
                            logger.info(f"      → {len(sel_events)} events")

                            if sel_idx < len(selections):
                                self.human_like_delay(2, 3)

                        except Exception as e:
                            logger.error(f"    Error parsing selection {selection['name']}: {e}")
                            continue
                else:
                    logger.info(f"  No selections found for {category['name']}")

            if config.PARSE_EVENT_DETAILS and all_events:
                logger.info(f"  Parsing event details for first {config.MAX_EVENTS_FOR_DETAILS} events...")
                events_to_detail = all_events[:config.MAX_EVENTS_FOR_DETAILS]

                for evt_idx, event in enumerate(events_to_detail, 1):
                    try:
                        logger.info(f"    Event {evt_idx}/{len(events_to_detail)}: {event['title'][:40]}...")

                        details = self.parse_event_details(event['url'])

                        if details:
                            event.update(details)
                            logger.debug(f"      Added details: {list(details.keys())}")

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
        all_events = []

        try:
            logger.info(f"Navigating to {config.BASE_URL}")
            self.driver.get(config.BASE_URL)
            self.human_like_delay(4, 6)

            if self.check_for_captcha():
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

                if not self.wait_for_captcha_solution(max_wait_seconds=180, skip_if_headless=True):
                    logger.error("Cannot continue - CAPTCHA not solved on main page")
                    if self.headless:
                        logger.warning("⏭️  Продолжаю в headless режиме, несмотря на CAPTCHA на главной странице")
                    else:
                        raise Exception("CAPTCHA не решена на главной странице")

                self.human_like_delay(3, 5)

            self.close_popups()

            categories = self.get_categories()

            if not categories:
                logger.warning("No categories found")
                return []

            categories_to_parse = categories

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

            if config.MAX_CATEGORIES and len(categories_to_parse) > config.MAX_CATEGORIES:
                categories_to_parse = categories_to_parse[:config.MAX_CATEGORIES]

            for idx, category in enumerate(categories_to_parse, 1):
                try:
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"Category {idx}/{len(categories_to_parse)}: {category['title']}")
                    logger.info(f"{'=' * 60}")

                    events = self.parse_category(category)
                    all_events.extend(events)
                    logger.info(f"✓ '{category['title']}': {len(events)} events")

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

