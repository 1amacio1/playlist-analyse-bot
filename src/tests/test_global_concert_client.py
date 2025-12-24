
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.clients.global_concert_client import (
    get_artist_events,
    convert_ticketmaster_to_afisha_format,
    TicketmasterError
)

class TestGetArtistEvents:
    
    
    @patch('src.clients.global_concert_client.requests.get')
    def test_successful_request(self, mock_get):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '_embedded': {
                'events': [
                    {
                        'name': 'Test Event',
                        'dates': {
                            'start': {'dateTime': '2024-03-15T19:00:00Z'},
                            'timezone': 'UTC'
                        },
                        '_embedded': {
                            'venues': [{
                                'name': 'Test Venue',
                                'city': {'name': 'Moscow'},
                                'country': {'name': 'Russia'}
                            }]
                        },
                        '_links': {
                            'self': {'href': 'https://example.com/event'}
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test_token'}):
            result = get_artist_events('Test Artist', api_token='test_token')
            assert len(result) == 1
            assert result[0]['artist_name'] == 'Test Artist'
            assert result[0]['event_name'] == 'Test Event'
            assert result[0]['venue'] == 'Test Venue'
            assert result[0]['city'] == 'Moscow'
            assert result[0]['source'] == 'ticketmaster'
    
    @patch('src.clients.global_concert_client.requests.get')
    def test_rate_limit_retry(self, mock_get):
        

        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            '_embedded': {'events': []}
        }
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test_token'}):
            with patch('src.clients.global_concert_client.time.sleep'):
                result = get_artist_events('Test Artist', api_token='test_token', retries=3)
                assert result == []
                assert mock_get.call_count == 2
    
    @patch('src.clients.global_concert_client.requests.get')
    def test_error_raises_exception(self, mock_get):
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test_token'}):
            with pytest.raises(TicketmasterError):
                get_artist_events('Test Artist', api_token='test_token')
    
    def test_no_token_raises_error(self):
        
        with patch.dict('os.environ', {}, clear=True):

            with patch('src.clients.global_concert_client.API_TOKEN', None):
                with pytest.raises(TicketmasterError, match="TICKETMASTER_API_TOKEN is not set"):
                    get_artist_events('Test Artist', api_token=None)
    
    def test_convert_ticketmaster_to_afisha_format_full(self):
        
        event = {
            'event_name': 'Test Event',
            'url': 'https://example.com/event',
            'city': 'Moscow',
            'venue': 'Test Venue',
            'datetime': '2024-03-15T19:00:00Z'
        }
        result = convert_ticketmaster_to_afisha_format(event)
        assert result['title'] == 'Test Event'
        assert result['source'] == 'ticketmaster'
    
    @patch('src.clients.global_concert_client.MongoClient')
    @patch('src.clients.global_concert_client.config')
    def test_get_artists_from_db(self, mock_config, mongo):
        
        mock_config.mongo_uri = 'mongodb://localhost:27017'
        client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        mongo.return_value = client
        client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = [
            {'artist_name': 'Artist 1'},
            {'artist_name': 'Artist 2'}
        ]
        
        from src.clients.global_concert_client import get_artists_from_db
        a = get_artists_from_db()
        
        assert len(a) == 2
        assert 'Artist 1' in a
        assert 'Artist 2' in a
    
    @patch('src.clients.global_concert_client.requests.get')
    def test_empty_events_list(self, mock_get):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '_embedded': {'events': []}
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test_token'}):
            result = get_artist_events('Test Artist', api_token='test_token')
            assert result == []

class TestConvertTicketmasterToAfishaFormat:
    
    
    def test_full_conversion(self):
        
        event = {
            'event_name': 'Test Event',
            'url': 'https://example.com/event',
            'city': 'Moscow',
            'venue': 'Test Venue',
            'datetime': '2024-03-15T19:00:00Z'
        }
        
        result = convert_ticketmaster_to_afisha_format(event)
        
        assert result['title'] == 'Test Event'
        assert result['url'] == 'https://example.com/event'
        assert result['category'] == 'concert'
        assert 'Moscow' in result['description']
        assert 'Test Venue' in result['description']
        assert result['venue'] == 'Test Venue'
        assert result['date'] == '2024-03-15T19:00:00Z'
        assert result['source'] == 'ticketmaster'
    
    def test_missing_fields(self):
        
        event = {}
        
        result = convert_ticketmaster_to_afisha_format(event)
        
        assert result['title'] == '-'
        assert result['url'] == '-'
        assert result['venue'] == '-'
        assert result['date'] == '-'
        assert result['source'] == 'ticketmaster'
    
    def test_partial_fields(self):
        
        event = {
            'event_name': 'Test Event',
            'venue': 'Test Venue'
        }
        
        result = convert_ticketmaster_to_afisha_format(event)
        
        assert result['title'] == 'Test Event'
        assert result['venue'] == 'Test Venue'
        assert result['url'] == '-'
        assert result['date'] == '-'

