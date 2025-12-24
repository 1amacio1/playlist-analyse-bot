from typing import List, Dict
import re
import logging
from src.repositories.concert_repository import ConcertRepository

logger = logging.getLogger(__name__)

class ConcertMatcherService:
    def __init__(self, repository: ConcertRepository, city: str = 'orenburg'):
        self.repository = repository
        self.city = city

    def normalize_name(self, name: str) -> str:
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def is_stop_word(self, word: str) -> bool:
        stop_words = {
            'в', 'на', 'и', 'с', 'для', 'от', 'из', 'по', 'к', 'о', 'а', 'но', 'или',
            'the', 'and', 'in', 'on', 'at', 'for', 'of', 'to', 'with', 'by',
            'концерт', 'концерты', 'шоу', 'stand', 'up', 'standup', 'стендап'
        }
        return word.lower() in stop_words

    def find_artist_in_text(self, artist_name: str, text: str) -> bool:
        if not text or not artist_name:
            return False

        normalized_artist = self.normalize_name(artist_name)
        normalized_text = text.lower()

        if len(normalized_artist.replace(' ', '')) < 3:
            return False

        artist_clean = re.sub(r'[^\w\s]', '', normalized_artist)
        text_clean = re.sub(r'[^\w\s]', '', normalized_text)

        if len(artist_clean) >= 4:
            pattern = r'\b' + re.escape(artist_clean) + r'\b'
            if re.search(pattern, text_clean):
                return True

        artist_words = [w for w in artist_clean.split() if len(w) >= 3 and not self.is_stop_word(w)]

        if len(artist_words) >= 2:
            words_found = sum(1 for word in artist_words if word in text_clean)

            if len(artist_words) == 2 and words_found >= 2:
                positions = []
                for word in artist_words:
                    pos = text_clean.find(word)
                    if pos != -1:
                        positions.append(pos)

                if len(positions) >= 2:
                    min_pos, max_pos = min(positions), max(positions)
                    if max_pos - min_pos < 100:
                        return True

            elif len(artist_words) >= 3 and words_found >= 2:
                return True

        elif len(artist_words) == 1:
            word = artist_words[0]
            if len(word) >= 4:
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, text_clean):
                    return True

        return False

    def is_from_city(self, concert: Dict) -> bool:
        url = concert.get('url', '')
        if not url:
            return False
        return f'/{self.city}/' in url

    def find_concerts_for_artists(self, artist_names: List[str]) -> Dict[str, List[Dict]]:
        logger.info(f"Searching for concerts matching {len(artist_names)} artists")

        all_concerts = self.repository.get_events_by_category('concert')
        logger.info(f"Found {len(all_concerts)} concerts in database")

        results = {}

        for artist_name in artist_names:
            matching_concerts = []

            for concert in all_concerts:
                if not self.is_from_city(concert):
                    continue
                title = concert.get('title', '')
                if title and self.find_artist_in_text(artist_name, title):
                    matching_concerts.append(concert)
                    continue

                full_title = concert.get('full_title', '')
                if full_title and self.find_artist_in_text(artist_name, full_title):
                    matching_concerts.append(concert)
                    continue

                description = concert.get('description', '')
                if description and len(description) > 20:
                    normalized_artist = self.normalize_name(artist_name)
                    artist_clean = re.sub(r'[^\w\s]', '', normalized_artist)
                    desc_clean = re.sub(r'[^\w\s]', '', description.lower())

                    if len(artist_clean) >= 4:
                        pattern = r'\b' + re.escape(artist_clean) + r'\b'
                        if re.search(pattern, desc_clean):
                            matching_concerts.append(concert)
                            continue

            if matching_concerts:
                results[artist_name] = matching_concerts
                logger.info(f"Found {len(matching_concerts)} concerts for {artist_name}")

        return results

    def get_all_matching_concerts(self, artist_names: List[str]) -> List[Dict]:
        artist_to_concerts = self.find_concerts_for_artists(artist_names)

        seen_urls = set()
        unique_concerts = []

        for concerts in artist_to_concerts.values():
            for concert in concerts:
                url = concert.get('url')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_concerts.append(concert)

        logger.info(f"Found {len(unique_concerts)} unique concerts matching artists")
        return unique_concerts

