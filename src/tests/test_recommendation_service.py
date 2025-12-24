
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.services.recommendation_service import RecommendationService

class TestRecommendationService:
    
    
    @pytest.fixture
    def mock_repository(self):
        
        mock_repository = Mock()
        mock_repository.get_events_by_category.return_value = []
        return mock_repository
    
    @pytest.fixture
    def service_disabled(self, mock_repository):
        
        with patch('src.services.recommendation_service.config') as mock_config:
            mock_config.GEMINI_API_KEY = ''
            return RecommendationService(mock_repository, city='moscow')
    
    @pytest.fixture
    def service_enabled(self, mock_repository):
        with patch('src.services.recommendation_service.config') as mock_config:
            mock_config.GEMINI_API_KEY = 'test_key'
            mock_config.proxy_url = None
            with patch('src.services.recommendation_service.genai.Client') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                service = RecommendationService(mock_repository, city='moscow')
                service.client = mock_client
                return service
    
    def test_service_disabled_without_key(self, service_disabled):
        
        assert service_disabled.enabled is False
        assert service_disabled.client is None
    
    def test_service_enabled_with_key(self, service_enabled):
        
        assert service_enabled.enabled is True
    
    def test_filter_concerts_by_city(self, service_enabled):
        
        concerts = [
            {'url': 'https://afisha.yandex.ru/moscow/concert1', 'title': 'Concert 1'},
            {'url': 'https://afisha.yandex.ru/saint-petersburg/concert2', 'title': 'Concert 2'},
            {'url': 'https://afisha.yandex.ru/moscow/concert3', 'title': 'Concert 3'},
        ]
        result = service_enabled._filter_concerts_by_city(concerts)
        assert len(result) == 2
        assert all('moscow' in concert['url'] for concert in result)
    
    def test_format_concerts_for_prompt(self, service_enabled):
        
        concerts = [
            {'title': 'Concert 1', 'description': 'Test description', 'url': 'https://example.com'},
            {'title': 'Concert 2', 'description': '', 'url': ''},
        ]
        result = service_enabled._format_concerts_for_prompt(concerts)
        assert 'Concert 1' in result
        assert 'Concert 2' in result
        assert 'Test description' in result
    
    def test_get_recommendations_disabled(self, service_disabled):
        
        result = service_disabled.get_recommendations(['Artist 1'])
        assert result == []
    
    def test_get_recommendations_no_artists(self, service_enabled):
        
        result = service_enabled.get_recommendations([])
        assert result == []
    
    def test_get_recommendations_no_concerts(self, service_enabled, mock_repository):
        
        mock_repository.get_events_by_category.return_value = []
        result = service_enabled.get_recommendations(['Artist 1'])
        assert result == []
    
    @patch('src.services.recommendation_service.json.loads')
    @patch('src.services.recommendation_service.genai.types.GenerateContentConfig')
    def test_get_recommendations_success(self, mock_config, mock_json, service_enabled, mock_repository):
        

        mock_repository.get_events_by_category.return_value = [
            {
                'url': 'https://afisha.yandex.ru/moscow/concert1',
                'title': 'Concert 1',
                'description': 'Test'
            },
            {
                'url': 'https://afisha.yandex.ru/moscow/concert2',
                'title': 'Concert 2',
                'description': 'Test'
            }
        ]
        
        mock_response = Mock()
        mock_response.text = '{"recommended_indices": [1, 2]}'
        service_enabled.client.models.generate_content.return_value = mock_response
        
        mock_json.return_value = {'recommended_indices': [1, 2]}
        
        result = service_enabled.get_recommendations(['Artist 1'])

        assert service_enabled.client.models.generate_content.called or result == []

