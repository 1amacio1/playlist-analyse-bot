import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # MongoDB settings
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password123')
    MONGO_DB = os.getenv('MONGO_DB', 'afisha_db')

    # Scraper settings
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    BASE_URL = 'https://afisha.yandex.ru/orenburg'

    # Browser settings - use real Chrome user agent
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    VIEWPORT = {'width': 1920, 'height': 1080}

    # Delays (in milliseconds)
    PAGE_LOAD_TIMEOUT = 60000
    WAIT_AFTER_LOAD = 2000
    SCROLL_DELAY = 800

    # Delays between categories (seconds)
    MIN_DELAY_BETWEEN_CATEGORIES = 8
    MAX_DELAY_BETWEEN_CATEGORIES = 15

    # CAPTCHA wait timeout (seconds)
    CAPTCHA_WAIT_TIMEOUT = int(os.getenv('CAPTCHA_WAIT_TIMEOUT', 120))

    # Categories to parse
    MAX_CATEGORIES = 6
    CATEGORIES_TO_PARSE = ['concert']

    # Selections (subcategories)
    PARSE_SELECTIONS = True
    MAX_SELECTIONS_PER_CATEGORY = 6

    # Event details
    PARSE_EVENT_DETAILS = False
    MAX_EVENTS_FOR_DETAILS = 10

    # Gemini API settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    @property
    def mongo_uri(self):
        return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"


config = Config()
