from typing import List, Dict, Optional
import logging
import json
import time
import os
import google.genai as genai
from google.genai import errors as genai_errors
from src.config.settings import config
from src.repositories.concert_repository import ConcertRepository

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, repository: ConcertRepository, city: str = 'orenburg'):
        self.repository = repository
        self.city = city
        self.api_key = config.GEMINI_API_KEY

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, recommendations will be disabled")
            self.enabled = False
            self.client = None
            self.model_name = None
            self.fallback_models = []
        else:
            proxy_url = config.proxy_url
            if proxy_url:
                os.environ['HTTP_PROXY'] = proxy_url
                os.environ['HTTPS_PROXY'] = proxy_url
                os.environ['http_proxy'] = proxy_url
                os.environ['https_proxy'] = proxy_url
                logger.info(f"Using proxy for Gemini API: {config.PROXY_HOST}:{config.PROXY_PORT}")
            else:
                os.environ.pop('HTTP_PROXY', None)
                os.environ.pop('HTTPS_PROXY', None)
                os.environ.pop('http_proxy', None)
                os.environ.pop('https_proxy', None)
                logger.info("No proxy configured for Gemini API")

            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-2.0-flash-exp'
            self.fallback_models = []
            self.enabled = True

    def _filter_concerts_by_city(self, concerts: List[Dict]) -> List[Dict]:
        filtered = []
        for concert in concerts:
            url = concert.get('url', '')
            if url and f'/{self.city}/' in url:
                filtered.append(concert)
        return filtered

    def _format_concerts_for_prompt(self, concerts: List[Dict]) -> str:
        formatted = []
        for i, concert in enumerate(concerts[:50], 1):
            title = concert.get('title', 'N/A')
            description = concert.get('description', '')
            url = concert.get('url', '')

            concert_info = f"{i}. {title}"
            if description:
                description_short = description[:200] + "..." if len(description) > 200 else description
                concert_info += f"\n   Описание: {description_short}"
            if url:
                concert_info += f"\n   URL: {url}"

            formatted.append(concert_info)

        return "\n".join(formatted)

    def get_recommendations(
        self,
        artist_names: List[str],
        max_recommendations: int = 10
    ) -> List[Dict]:
        if not self.enabled:
            logger.warning("Recommendations disabled - GEMINI_API_KEY not set")
            return []

        if not artist_names:
            logger.warning("No artists provided for recommendations")
            return []

        try:
            all_concerts = self.repository.get_events_by_category('concert')
            city_concerts = self._filter_concerts_by_city(all_concerts)

            if not city_concerts:
                logger.warning(f"No concerts found for city: {self.city}")
                return []

            logger.info(f"Analyzing {len(city_concerts)} concerts for recommendations")

            artists_str = ", ".join(artist_names[:20])
            concerts_str = self._format_concerts_for_prompt(city_concerts)

            prompt = f"""Ты музыкальный эксперт. Проанализируй стиль музыки исполнителей из плейлиста пользователя и порекомендуй концерты, которые могут быть интересны.

Исполнители из плейлиста:
{artists_str}

Доступные концерты в городе {self.city}:
{concerts_str}

Проанализируй музыкальные стили исполнителей и найди концерты, которые могут быть интересны пользователю.
Учти:
1. Музыкальные жанры и стили
2. Похожих исполнителей или группы в том же направлении
3. Связанные музыкальные сцены

Верни JSON массив с номерами рекомендованных концертов (только числа, без точек), максимум {max_recommendations} рекомендаций.
Формат ответа должен быть строго в формате JSON:
{{"recommended_indices": [1, 5, 12, ...]}}

ВАЖНО: Ответь только JSON объектом, без дополнительного текста, объяснений или markdown форматирования."""

            generation_config = genai.types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=1024,
            )

            max_retries = 3
            retry_delay = 20
            response = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to generate content with model: {self.model_name} (attempt {attempt + 1}/{max_retries})")
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=generation_config
                    )
                    logger.info(f"Successfully generated content with model: {self.model_name}")
                    break
                except genai_errors.ClientError as e:
                    error_str = str(e)
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                        if attempt < max_retries - 1:
                            logger.warning(f"Quota exceeded, waiting {retry_delay} seconds before retry...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"Quota exceeded after {max_retries} attempts. Please wait or check your API quota.")
                            last_error = e
                            break
                    else:
                        logger.error(f"API error: {e}")
                        last_error = e
                        break
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    last_error = e
                    break

            if response is None:
                error_msg = f"Could not generate content with model {self.model_name}"
                if last_error:
                    error_msg += f". Error: {last_error}"
                logger.error(error_msg)
                return []

            response_text = response.text.strip()

            logger.info(f"Gemini API response: {response_text[:200]}...")

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    result = json.loads(json_str)
                    recommended_indices = result.get('recommended_indices', [])
                    recommended_indices = [int(idx) for idx in recommended_indices if isinstance(idx, (int, str)) and str(idx).isdigit()]
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error: {e}. Response: {response_text[:500]}")
                    return []
            else:
                logger.warning(f"Could not find JSON in response: {response_text[:500]}")
                return []

            recommended_concerts = []
            seen_urls = set()

            for idx in recommended_indices:
                if 1 <= idx <= len(city_concerts):
                    concert = city_concerts[idx - 1]
                    url = concert.get('url')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        recommended_concerts.append(concert)
                        if len(recommended_concerts) >= max_recommendations:
                            break

            logger.info(f"Found {len(recommended_concerts)} recommended concerts")
            return recommended_concerts

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}", exc_info=True)
            return []
