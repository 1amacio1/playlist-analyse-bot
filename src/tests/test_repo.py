import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from src.repositories.concert_repository import ConcertRepository

def test_repo_methods():
    assert hasattr(ConcertRepository, 'save_event')
    assert hasattr(ConcertRepository, 'get_events_by_category')

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.async_session_maker')
async def test_repo_init(mock_session_maker):
    session = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = session
    mock_session_maker.return_value.__aexit__.return_value = None
    r = ConcertRepository()
    assert r is not None

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_event(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    event = {'url': 'http://test.com', 'title': 'Test'}
    res = await r.save_event(event)
    assert res is True
    session.add.assert_called_once()
    session.commit.assert_called_once()

@patch('src.repositories.concert_repository.ConcertRepository._get_session')
def test_get_events(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    event1 = Mock()
    event1.to_dict.return_value = {'title': 'T1', 'category': 'concert'}
    event2 = Mock()
    event2.to_dict.return_value = {'title': 'T2', 'category': 'concert'}
    result.scalars.return_value.all.return_value = [event1, event2]
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = r.get_events_by_category('concert')
    assert len(res) == 2

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_event_by_url(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    event = Mock()
    event.to_dict.return_value = {'title': 'T', 'url': 'http://test.com'}
    result.scalar_one_or_none.return_value = event
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.get_event_by_url('http://test.com')
    assert res['title'] == 'T'

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_duplicate(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock(side_effect=IntegrityError('duplicate', None, None))
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    event = {'url': 'http://test.com', 'title': 'Test'}
    res = await r.save_event(event)
    assert res is False
    session.rollback.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_all_events(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    event = Mock()
    event.to_dict.return_value = {'title': 'T1'}
    result.scalars.return_value.all.return_value = [event]
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.get_all_events()
    assert len(res) == 1

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_count_events(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 5
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.count_events()
    assert res == 5

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_batch(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    events = [{'url': 'http://test1.com'}, {'url': 'http://test2.com'}]
    res = await r.save_events_batch(events)
    assert res == 2
    assert session.add.call_count == 2
    session.commit.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_batch_no_url(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    events = [{'title': 'Test'}, {'url': 'http://test.com'}]
    res = await r.save_events_batch(events)
    assert res == 1
    session.add.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_batch_duplicate(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    result = MagicMock()
    event = Mock()
    result.scalar_one_or_none.return_value = event
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    events = [{'url': 'http://test.com'}, {'url': 'http://test.com'}]
    res = await r.save_events_batch(events)
    assert res == 0
    session.add.assert_not_called()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_batch_error(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock(side_effect=Exception('Error'))
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    events = [{'url': 'http://test.com'}]
    res = await r.save_events_batch(events)
    assert res == 1
    session.rollback.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_save_event_error(mock_get_session):
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock(side_effect=Exception('Error'))
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    event = {'url': 'http://test.com', 'title': 'Test'}
    res = await r.save_event(event)
    assert res is False
    session.rollback.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_event_by_url_none(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.get_event_by_url('http://test.com')
    assert res is None

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_event_by_url_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.get_event_by_url('http://test.com')
    assert res is None

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_count_events_by_category(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 3
    session.execute = AsyncMock(return_value=result)
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.count_events_by_category('concert')
    assert res == 3

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_count_events_by_category_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.count_events_by_category('concert')
    assert res == 0

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_count_events_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.count_events()
    assert res == 0

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_all_events_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.get_all_events()
    assert res == []

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_delete_all_events(mock_get_session):
    session = AsyncMock()
    result = MagicMock()
    result.rowcount = 5
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.delete_all_events()
    assert res == 5
    session.commit.assert_called_once()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_delete_all_events_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = await r.delete_all_events()
    assert res == 0
    session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_close():
    session = AsyncMock()
    session.close = AsyncMock()
    r = ConcertRepository(session=session)
    await r.close()
    session.close.assert_called_once()

def test_connect():
    r = ConcertRepository()
    r.connect()
    assert True

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository._get_session')
async def test_get_events_by_category_error(mock_get_session):
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception('Error'))
    session.close = AsyncMock()
    mock_get_session.return_value = session
    
    r = ConcertRepository()
    res = r.get_events_by_category('concert')
    assert res == []
