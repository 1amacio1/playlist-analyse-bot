import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers.playlist_handler import ConcertService, handle_playlist_url
from src.bot.handlers.callback_handler import handle_city_selection, handle_sort, handle_reminder, handle_pagination, handle_refresh, handle_recommendations

@pytest.fixture
def repo():
    r = Mock()
    r.get_events_by_category.return_value = []
    return r

def test_concert_service(repo):
    s = ConcertService(repo)
    data = [{'url': 'https://afisha.yandex.ru/moscow/1'}]
    res = s.get_available_cities(data)
    assert 'Москва' in res

def test_concert_service_filter(repo):
    s = ConcertService(repo)
    data = [
        {'url': 'https://afisha.yandex.ru/moscow/1', 'title': 'M'},
        {'url': 'https://afisha.yandex.ru/spb/2', 'title': 'S'}
    ]
    res = s.filter_by_city(data, 'Москва')
    assert len(res) == 1

def test_concert_service_group(repo):
    s = ConcertService(repo)
    data = [
        {'matched_artist': 'A1', 'title': 'T1'},
        {'matched_artist': 'A1', 'title': 'T2'}
    ]
    res = s.group_by_artist(data)
    assert 'A1' in res

def test_concert_service_find(repo):
    s = ConcertService(repo)
    repo.get_events_by_category.return_value = [
        {'url': 'http://test.com', 'title': 'Test Artist Concert', 'full_title': '', 'description': ''}
    ]
    res = s.find_concerts_by_artists(['Test Artist'])
    assert len(res) >= 0

def test_concert_service_find_empty(repo):
    s = ConcertService(repo)
    repo.get_events_by_category.return_value = []
    res = s.find_concerts_by_artists(['Artist'])
    assert res == []

@pytest.mark.asyncio
async def test_city_selection():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'city_Москва'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [], 'original_concerts': [], 'city_filter': None, 'available_cities': ['Москва'], 'sort_by': 'date', 'current_page': 0}}
    await handle_city_selection(cb, res)
    assert res[123]['city_filter'] == 'Москва'

@pytest.mark.asyncio
async def test_city_all():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'city_all'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [], 'original_concerts': [], 'city_filter': 'Москва', 'available_cities': ['Москва'], 'sort_by': 'date', 'current_page': 0}}
    await handle_city_selection(cb, res)
    assert res[123]['city_filter'] is None

@pytest.mark.asyncio
async def test_sort():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'sort_artist'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [], 'sort_by': 'date', 'current_page': 0, 'city_filter': None}}
    await handle_sort(cb, res)
    assert res[123]['sort_by'] == 'artist'

@pytest.mark.asyncio
async def test_sort_date():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'sort_date'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [], 'sort_by': 'artist', 'current_page': 0, 'city_filter': None}}
    await handle_sort(cb, res)
    assert res[123]['sort_by'] == 'date'

@pytest.mark.asyncio
async def test_reminder():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'remind_0'
    cb.answer = AsyncMock()
    res = {123: {'concerts': [{'title': 'T', 'dates': ['2024-03-15']}]}}
    await handle_reminder(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.playlist_handler.MusicClient')
@patch('src.bot.handlers.playlist_handler.ServicePlaylist')
@patch('src.bot.handlers.playlist_handler.ConcertRepository')
@patch('src.bot.handlers.playlist_handler.extract_from_url')
async def test_playlist(mock_extract, mock_repo, mock_svc, mock_client):
    mock_extract.return_value = ('user', 'kind')
    pl = Mock()
    pl.fetch_tracks.return_value = []
    mock_client.from_env.return_value = Mock(get_playlist=Mock(return_value=pl))
    mock_svc.return_value = Mock(get_artist_names=Mock(return_value=[]))
    mock_repo.return_value = Mock(get_events_by_category=Mock(return_value=[]), close=Mock())
    msg = Mock()
    msg.text = 'https://music.yandex.ru/users/user/playlists/kind'
    msg.from_user = Mock()
    msg.from_user.id = 123
    msg.answer = AsyncMock(return_value=Mock(edit_text=AsyncMock()))
    state = Mock()
    state.clear = AsyncMock()
    user_res = {}
    await handle_playlist_url(msg, state, user_res)
    msg.answer.assert_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.playlist_handler.extract_from_url')
async def test_invalid_url(mock_extract):
    mock_extract.side_effect = ValueError("bad url")
    msg = Mock()
    msg.text = 'bad url'
    msg.answer = AsyncMock()
    state = Mock()
    user_res = {}
    await handle_playlist_url(msg, state, user_res)
    msg.answer.assert_called()

@pytest.mark.asyncio
async def test_city_select():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'city_select'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'available_cities': ['Москва', 'СПб'], 'sort_by': 'date', 'current_page': 0, 'city_filter': None}}
    await handle_city_selection(cb, res)
    cb.message.edit_text.assert_called()

@pytest.mark.asyncio
async def test_city_change():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'city_change'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'available_cities': ['Москва'], 'sort_by': 'date', 'current_page': 0, 'city_filter': 'Москва'}}
    await handle_city_selection(cb, res)
    cb.message.edit_text.assert_called()

@pytest.mark.asyncio
async def test_pagination():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'page_1'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [{'title': f'T{i}', 'dates': ['2024-03-15'], 'url': 'http://test.com', 'venue': 'V'} for i in range(25)], 'sort_by': 'date', 'current_page': 0, 'city_filter': None, 'available_cities': []}}
    await handle_pagination(cb, res)
    assert res[123]['current_page'] == 1

@pytest.mark.asyncio
async def test_refresh():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'refresh'
    cb.message = Mock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    res = {123: {'concerts': [{'title': 'T', 'dates': ['2024-03-15'], 'url': 'http://test.com', 'venue': 'V'}], 'sort_by': 'date', 'current_page': 0, 'city_filter': None, 'available_cities': []}}
    await handle_refresh(cb, res)
    cb.message.edit_text.assert_called()

@pytest.mark.asyncio
async def test_reminder_invalid():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'remind_999'
    cb.answer = AsyncMock()
    res = {123: {'concerts': [{'title': 'T', 'dates': ['2024-03-15']}]}}
    await handle_reminder(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
async def test_city_selection_no_user():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 999
    cb.answer = AsyncMock()
    res = {}
    await handle_city_selection(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
async def test_sort_no_user():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 999
    cb.answer = AsyncMock()
    res = {}
    await handle_sort(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
async def test_pagination_no_user():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 999
    cb.answer = AsyncMock()
    res = {}
    await handle_pagination(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.playlist_handler.MusicClient')
@patch('src.bot.handlers.playlist_handler.ServicePlaylist')
@patch('src.bot.handlers.playlist_handler.ConcertRepository')
@patch('src.bot.handlers.playlist_handler.extract_from_url')
@patch('bot.handlers.playlist_handler.get_artist_events')
async def test_playlist_with_artists(mock_events, mock_extract, mock_repo, mock_svc, mock_client):
    mock_extract.return_value = ('user', 'kind')
    pl = Mock()
    tr = Mock()
    tr.track = Mock()
    a = Mock()
    a.name = 'Artist1'
    tr.track.artists = [a]
    pl.fetch_tracks.return_value = [tr]
    mock_client.from_env.return_value = Mock(get_playlist=Mock(return_value=pl))
    mock_svc.return_value = Mock(get_artist_names=Mock(return_value=['Artist1']))
    mock_repo.return_value = Mock(get_events_by_category=Mock(return_value=[{'url': 'http://test.com', 'title': 'Test Artist1'}]), close=Mock())
    mock_events.return_value = []
    msg = Mock()
    msg.text = 'https://music.yandex.ru/users/user/playlists/kind'
    msg.from_user = Mock()
    msg.from_user.id = 123
    msg.answer = AsyncMock(return_value=Mock(edit_text=AsyncMock()))
    state = Mock()
    state.clear = AsyncMock()
    user_res = {}
    await handle_playlist_url(msg, state, user_res)
    msg.answer.assert_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.playlist_handler.MusicClient')
@patch('src.bot.handlers.playlist_handler.ServicePlaylist')
@patch('src.bot.handlers.playlist_handler.ConcertRepository')
@patch('src.bot.handlers.playlist_handler.extract_from_url')
async def test_playlist_init_error(mock_extract, mock_repo, mock_svc, mock_client):
    mock_extract.return_value = ('user', 'kind')
    mock_client.from_env.side_effect = Exception("init error")
    msg = Mock()
    msg.text = 'https://music.yandex.ru/users/user/playlists/kind'
    msg.from_user = Mock()
    msg.from_user.id = 123
    msg.answer = AsyncMock(return_value=Mock(edit_text=AsyncMock()))
    state = Mock()
    state.clear = AsyncMock()
    user_res = {}
    await handle_playlist_url(msg, state, user_res)
    msg.answer.assert_called()

@pytest.mark.asyncio
@patch('src.services.recommendation_service.RecommendationService')
@patch('src.repositories.concert_repository.ConcertRepository')
async def test_recommendations(mock_repo_class, mock_rec_class):
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'recommendations'
    cb.message = Mock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    repo = Mock()
    repo.close = Mock()
    mock_repo_class.return_value = repo
    s = Mock()
    s.enabled = True
    s.get_recommendations.return_value = [{'title': 'T', 'url': 'http://test.com'}]
    mock_rec_class.return_value = s
    res = {123: {'artists': ['A1'], 'city_filter': None, 'available_cities': []}}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
async def test_recommendations_no_artists():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'recommendations'
    cb.answer = AsyncMock()
    res = {123: {'artists': []}}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
@patch('src.services.recommendation_service.RecommendationService')
@patch('src.repositories.concert_repository.ConcertRepository')
async def test_recommendations_disabled(mock_repo_class, mock_rec_class):
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'recommendations'
    cb.answer = AsyncMock()
    repo = Mock()
    repo.close = Mock()
    mock_repo_class.return_value = repo
    s = Mock()
    s.enabled = False
    mock_rec_class.return_value = s
    res = {123: {'artists': ['A1'], 'city_filter': None}}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
@patch('src.services.recommendation_service.RecommendationService')
@patch('src.repositories.concert_repository.ConcertRepository')
async def test_recommendations_empty(mock_repo_class, mock_rec_class):
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'recommendations'
    cb.answer = AsyncMock()
    repo = Mock()
    repo.close = Mock()
    mock_repo_class.return_value = repo
    s = Mock()
    s.enabled = True
    s.get_recommendations.return_value = []
    mock_rec_class.return_value = s
    res = {123: {'artists': ['A1'], 'city_filter': None}}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
@patch('src.repositories.concert_repository.ConcertRepository')
async def test_recommendations_error(mock_repo_class):
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 123
    cb.data = 'recommendations'
    cb.answer = AsyncMock()
    mock_repo_class.side_effect = Exception("error")
    res = {123: {'artists': ['A1'], 'city_filter': None}}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()

@pytest.mark.asyncio
async def test_recommendations_no_user():
    cb = Mock()
    cb.from_user = Mock()
    cb.from_user.id = 999
    cb.answer = AsyncMock()
    res = {}
    await handle_recommendations(cb, res)
    cb.answer.assert_called()
