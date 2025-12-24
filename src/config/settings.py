import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_USERNAME = os.getenv('DB_USERNAME', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_NAME = os.getenv('DB_NAME', 'afisha_db')

    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password123')
    MONGO_DB = os.getenv('MONGO_DB', 'afisha_db')

    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    CITY = os.getenv('CITY', 'orenburg')

    @property
    def BASE_URL(self):
        return f'https://afisha.yandex.ru/{self.CITY}'

    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    VIEWPORT = {'width': 1920, 'height': 1080}

    PAGE_LOAD_TIMEOUT = 60000
    WAIT_AFTER_LOAD = 2000
    SCROLL_DELAY = 800

    MIN_DELAY_BETWEEN_CATEGORIES = 8
    MAX_DELAY_BETWEEN_CATEGORIES = 15

    CAPTCHA_WAIT_TIMEOUT = int(os.getenv('CAPTCHA_WAIT_TIMEOUT', 120))

    MAX_CATEGORIES = 6
    CATEGORIES_TO_PARSE = ['concert']

    PARSE_SELECTIONS = True
    MAX_SELECTIONS_PER_CATEGORY = 6

    PARSE_EVENT_DETAILS = False
    MAX_EVENTS_FOR_DETAILS = 10

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    PROXY_HOST = os.getenv('PROXY_HOST', '')
    PROXY_PORT = os.getenv('PROXY_PORT', '')
    PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
    PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')

    @property
    def proxy_url(self):
        if not all([self.PROXY_HOST, self.PROXY_PORT, self.PROXY_USERNAME, self.PROXY_PASSWORD]):
            return None
        return f"http://{self.PROXY_USERNAME}:{self.PROXY_PASSWORD}@{self.PROXY_HOST}:{self.PROXY_PORT}"

    @property
    def proxies_dict(self):
        proxy_url = self.proxy_url
        if proxy_url is None:
            return None
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    @property
    def mongo_uri(self):
        return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"

config = Config()
