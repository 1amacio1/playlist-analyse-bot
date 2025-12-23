import pytest
from unittest.mock import Mock, patch, MagicMock
from src.repositories.concert_repository import ConcertRepository

def test_repo_methods():
    assert hasattr(ConcertRepository, 'save_event')
    assert hasattr(ConcertRepository, 'get_events_by_category')

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_repo_init(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.admin.command.return_value = None
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    mock_mongo.return_value = mc
    r = ConcertRepository()
    assert r is not None

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_save_event(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find_one.return_value = None
    coll.insert_one.return_value = Mock(inserted_id='123')
    mock_mongo.return_value = mc
    r = ConcertRepository()
    event = {'url': 'http://test.com', 'title': 'Test'}
    r.save_event(event)
    coll.insert_one.assert_called()

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_get_events(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find.return_value = [{'title': 'T1'}, {'title': 'T2'}]
    mock_mongo.return_value = mc
    r = ConcertRepository()
    res = r.get_events_by_category('concert')
    assert len(res) == 2

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_get_event_by_url(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find_one.return_value = {'title': 'T', 'url': 'http://test.com'}
    mock_mongo.return_value = mc
    r = ConcertRepository()
    res = r.get_event_by_url('http://test.com')
    assert res['title'] == 'T'

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_save_duplicate(mock_config, mock_mongo):
    from pymongo.errors import DuplicateKeyError
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find_one.return_value = {'url': 'http://test.com'}
    coll.insert_one.side_effect = DuplicateKeyError('duplicate')
    mock_mongo.return_value = mc
    r = ConcertRepository()
    event = {'url': 'http://test.com', 'title': 'Test'}
    res = r.save_event(event)
    assert res is False

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_get_all_events(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find.return_value = [{'title': 'T1'}]
    mock_mongo.return_value = mc
    r = ConcertRepository()
    res = r.get_all_events()
    assert len(res) == 1

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_count_events(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.count_documents.return_value = 5
    mock_mongo.return_value = mc
    r = ConcertRepository()
    res = r.count_events()
    assert res == 5

@patch('src.repositories.concert_repository.MongoClient')
@patch('src.repositories.concert_repository.config')
def test_save_batch(mock_config, mock_mongo):
    mock_config.mongo_uri = 'mongodb://localhost:27017'
    mock_config.MONGO_DB = 'test'
    mc = MagicMock()
    db = MagicMock()
    coll = MagicMock()
    mc.__getitem__.return_value = db
    db.__getitem__.return_value = coll
    coll.find_one.return_value = None
    coll.insert_one.return_value = Mock(inserted_id='123')
    mock_mongo.return_value = mc
    r = ConcertRepository()
    events = [{'url': 'http://test1.com'}, {'url': 'http://test2.com'}]
    res = r.save_events_batch(events)
    assert res == 2
