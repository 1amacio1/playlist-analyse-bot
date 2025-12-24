import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from src.db.database import get_database_url, get_session, init_db, close_db

@patch('src.db.database.config')
def test_get_database_url(mock_config):
    mock_config.DB_USERNAME = 'test_user'
    mock_config.DB_PASSWORD = 'test_pass'
    mock_config.DB_HOST = 'test_host'
    mock_config.DB_PORT = 5432
    mock_config.DB_NAME = 'test_db'
    url = get_database_url()
    assert 'test_user' in url
    assert 'test_pass' in url
    assert 'test_host' in url
    assert 'test_db' in url
    assert 'postgresql+asyncpg' in url

@pytest.mark.asyncio
@patch('src.db.database.async_session_maker')
async def test_get_session(mock_session_maker):
    session = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = session
    mock_session_maker.return_value.__aexit__.return_value = None
    
    async for s in get_session():
        assert s == session
        break

@pytest.mark.asyncio
@patch('src.db.database.engine')
async def test_init_db(mock_engine):
    conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = conn
    mock_engine.begin.return_value.__aexit__.return_value = None
    conn.run_sync = AsyncMock()
    
    await init_db()
    conn.run_sync.assert_called_once()

@pytest.mark.asyncio
@patch('src.db.database.engine')
async def test_close_db(mock_engine):
    mock_engine.dispose = AsyncMock()
    await close_db()
    mock_engine.dispose.assert_called_once()
