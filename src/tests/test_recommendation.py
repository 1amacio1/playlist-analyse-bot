import pytest
from unittest.mock import Mock, patch
from src.services.recommendation_service import RecommendationService

@pytest.fixture
def repo():
    r = Mock()
    r.get_events_by_category.return_value = []
    return r

def test_disabled(repo):
    with patch('src.services.recommendation_service.config') as cfg:
        cfg.GEMINI_API_KEY = ''
        s = RecommendationService(repo, city='moscow')
        assert s.enabled is False

def test_enabled(repo):
    with patch('src.services.recommendation_service.config') as cfg:
        cfg.GEMINI_API_KEY = 'key'
        cfg.proxy_url = 'http://proxy:8080'
        cfg.PROXY_HOST = 'proxy'
        cfg.PROXY_PORT = 8080
        with patch('src.services.recommendation_service.genai.Client'):
            s = RecommendationService(repo, city='moscow')
            assert s.enabled is True

def test_filter(repo):
    with patch('src.services.recommendation_service.config') as cfg:
        cfg.GEMINI_API_KEY = 'key'
        cfg.proxy_url = 'http://proxy:8080'
        cfg.PROXY_HOST = 'proxy'
        cfg.PROXY_PORT = 8080
        with patch('src.services.recommendation_service.genai.Client'):
            s = RecommendationService(repo, city='moscow')
            data = [
                {'url': 'https://afisha.yandex.ru/moscow/1'},
                {'url': 'https://afisha.yandex.ru/spb/2'}
            ]
            res = s._filter_concerts_by_city(data)
            assert len(res) == 1

def test_get_empty(repo):
    with patch('src.services.recommendation_service.config') as cfg:
        cfg.GEMINI_API_KEY = ''
        s = RecommendationService(repo, city='moscow')
        res = s.get_recommendations(['A'])
        assert res == []

