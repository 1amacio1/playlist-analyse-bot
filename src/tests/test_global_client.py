import pytest
from unittest.mock import Mock, patch, MagicMock
from src.clients.global_concert_client import get_artist_events, convert_ticketmaster_to_afisha_format, TicketmasterError

@patch('src.clients.global_concert_client.requests.get')
def test_get_events(mock_get):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {'_embedded': {'events': []}}
    mock_get.return_value = resp
    with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test'}):
        res = get_artist_events('Artist', api_token='test')
        assert res == []

@patch('src.clients.global_concert_client.requests.get')
def test_get_events_with_data(mock_get):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        '_embedded': {
            'events': [{
                'name': 'Event',
                'dates': {'start': {'dateTime': '2024-03-15T19:00:00Z'}},
                '_embedded': {'venues': [{'name': 'V', 'city': {'name': 'M'}, 'country': {'name': 'R'}}]},
                '_links': {'self': {'href': 'http://test.com'}}
            }]
        }
    }
    mock_get.return_value = resp
    with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test'}):
        res = get_artist_events('Artist', api_token='test')
        assert len(res) == 1

def test_convert():
    event = {'event_name': 'Test', 'url': 'http://test.com', 'city': 'Moscow', 'venue': 'V', 'datetime': '2024-03-15T19:00:00Z'}
    res = convert_ticketmaster_to_afisha_format(event)
    assert res['title'] == 'Test'
    assert res['source'] == 'ticketmaster'

def test_convert_empty():
    res = convert_ticketmaster_to_afisha_format({})
    assert res['title'] == '-'

def test_convert_empty_venue():
    event = {'event_name': 'Test', 'url': 'http://test.com', 'city': 'Moscow', 'venue': '', 'datetime': '2024-03-15T19:00:00Z'}
    res = convert_ticketmaster_to_afisha_format(event)
    assert res['venue'] == ''

def test_convert_no_datetime():
    event = {'event_name': 'Test', 'url': 'http://test.com', 'city': 'Moscow', 'venue': 'V', 'datetime': ''}
    res = convert_ticketmaster_to_afisha_format(event)
    assert res['date'] == ''

def test_no_token():
    with patch.dict('os.environ', {}, clear=True):
        with patch('src.clients.global_concert_client.API_TOKEN', None):
            with pytest.raises(TicketmasterError):
                get_artist_events('Artist', api_token=None)

@patch('src.clients.global_concert_client.MongoClient')
@patch('src.clients.global_concert_client.config')
def test_get_artists_db(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find.return_value = [{'artist_name': 'A1'}, {'artist_name': 'A2'}]
    mock_mongo.return_value = mc
    from src.clients.global_concert_client import get_artists_from_db
    res = get_artists_from_db()
    assert len(res) == 2

@patch('src.clients.global_concert_client.requests.get')
def test_rate_limit(mock_get):
    resp1 = Mock()
    resp1.status_code = 429
    resp2 = Mock()
    resp2.status_code = 200
    resp2.json.return_value = {'_embedded': {'events': []}}
    mock_get.side_effect = [resp1, resp2]
    with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test'}):
        with patch('src.clients.global_concert_client.time.sleep'):
            res = get_artist_events('Artist', api_token='test', retries=3)
            assert res == []

@patch('src.clients.global_concert_client.requests.get')
def test_error(mock_get):
    resp = Mock()
    resp.status_code = 500
    mock_get.return_value = resp
    with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test'}):
        with pytest.raises(TicketmasterError):
            get_artist_events('Artist', api_token='test', retries=1)

@patch('src.clients.global_concert_client.requests.get')
def test_no_embedded(mock_get):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {}
    mock_get.return_value = resp
    with patch.dict('os.environ', {'TICKETMASTER_API_TOKEN': 'test'}):
        res = get_artist_events('Artist', api_token='test')
        assert res == []
